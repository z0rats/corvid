import { render, screen, fireEvent, within, waitFor } from '@testing-library/react';
import { MemoryRouter, Routes, Route, useLocation } from 'react-router';
import { Provider, createStore } from 'jotai';
import { ThemeProvider } from '@mui/material/styles';
import { lightTheme } from '../../../../core/config/theme';
import SingleLookup from './SingleLookup';
import { iocLookupApi } from '../../shared/services/api/iocLookupApi';
import { lookupHistoryApi } from './services/api/lookupHistoryApi';
import { clearLookupCache } from './utils/lookupCache';

vi.mock('../../shared/services/api/iocLookupApi', () => ({
  iocLookupApi: { fetchServiceDefinitions: vi.fn(), lookupSingleService: vi.fn(), fetchNewsfeedMentions: vi.fn() },
}));
vi.mock('./services/api/lookupHistoryApi', () => ({ lookupHistoryApi: { saveSearch: vi.fn() } }));

const DEFINITIONS = {
  virustotal: { name: 'VirusTotal', supportedIocTypes: ['IPv4', 'Domain'], isAvailable: true },
  abuseipdb: { name: 'AbuseIPDB', supportedIocTypes: ['IPv4'], isAvailable: true },
  shodan: { name: 'Shodan', supportedIocTypes: ['IPv4'], isAvailable: false },
  // a backend provider the frontend has no detail component for
  newprovider: { name: 'New Provider', supportedIocTypes: ['IPv4'], isAvailable: true },
};

const RESPONSES = {
  virustotal: { data: { data: { attributes: { last_analysis_stats: { harmless: 60, malicious: 4, suspicious: 0, undetected: 6 } } } } },
  abuseipdb: { data: { data: { abuseConfidenceScore: 100 } } },
  newprovider: { error: 'Rate limited', status: 429 },
};

function LocationProbe() {
  const location = useLocation();
  return <div>{`at ${location.pathname}${location.search}`}</div>;
}

function renderPage(path = '/ioc-tools/lookup') {
  return render(
    <ThemeProvider theme={lightTheme}>
      <Provider store={createStore()}>
        <MemoryRouter initialEntries={[path]}>
          <Routes>
            <Route path="/ioc-tools/lookup" element={<SingleLookup />} />
            <Route path="*" element={<LocationProbe />} />
          </Routes>
        </MemoryRouter>
      </Provider>
    </ThemeProvider>,
  );
}

function search(value) {
  const input = screen.getByPlaceholderText(/Enter an IOC to analyze/);
  fireEvent.change(input, { target: { value } });
  fireEvent.click(screen.getByRole('button', { name: 'Analyze' }));
}

const row = (name) => screen.getByText(name).closest('tr');

beforeEach(() => {
  clearLookupCache();
  iocLookupApi.fetchServiceDefinitions.mockResolvedValue(DEFINITIONS);
  iocLookupApi.lookupSingleService.mockImplementation(async (key) => RESPONSES[key]);
  iocLookupApi.fetchNewsfeedMentions.mockResolvedValue({ count: 0, articles: [] });
  lookupHistoryApi.saveSearch.mockResolvedValue({ id: 1 });
});
afterEach(() => vi.clearAllMocks());

describe('SingleLookup', () => {
  it('starts on the welcome screen and rejects unsupported input', async () => {
    renderPage();
    search('definitely not an ioc');
    expect(await screen.findByText('Invalid Input')).toBeInTheDocument();
    expect(iocLookupApi.lookupSingleService).not.toHaveBeenCalled();
  });

  it('queries every available provider for the detected type and shows verdicts', async () => {
    renderPage();
    search('45.33.32.156');
    expect(await screen.findByText('Detected as malicious or suspicious by 4/70 engines')).toBeInTheDocument();
    expect(await screen.findByText('Abuse Score: 100%')).toBeInTheDocument();
    expect(screen.queryByText('Shodan')).toBeNull(); // not available
    const calls = iocLookupApi.lookupSingleService.mock.calls.map(([key, ioc, type]) => [key, ioc, type]);
    expect(calls).toEqual(expect.arrayContaining([
      ['virustotal', '45.33.32.156', 'IPv4'],
      ['abuseipdb', '45.33.32.156', 'IPv4'],
      ['newprovider', '45.33.32.156', 'IPv4'],
    ]));
  });

  it('refangs defanged input before looking it up', async () => {
    renderPage();
    search('45[.]33[.]32[.]156');
    await screen.findByText('Abuse Score: 100%');
    expect(iocLookupApi.lookupSingleService).toHaveBeenCalledWith('abuseipdb', '45.33.32.156', 'IPv4', expect.anything());
  });

  it('saves one history entry once every provider has answered', async () => {
    renderPage();
    search('45.33.32.156');
    await waitFor(() => expect(lookupHistoryApi.saveSearch).toHaveBeenCalledTimes(1));
    const [ioc, type, results] = lookupHistoryApi.saveSearch.mock.calls[0];
    expect([ioc, type]).toEqual(['45.33.32.156', 'IPv4']);
    expect(results.map((r) => [r.service_key, r.status])).toEqual([
      ['virustotal', 'found'], ['abuseipdb', 'found'], ['newprovider', 'error'],
    ]);
  });

  it('an error row can be expanded to show the rate-limit details', async () => {
    // Regression: error rows without a detail component could not be expanded at all
    RESPONSES.newprovider = { error: 'Quota exceeded', status: 429 };
    iocLookupApi.lookupSingleService.mockImplementation(async (key) => (
      key === 'newprovider'
        ? { data: { error: 429, is_rate_limited: true, message: 'Daily quota used', retry_after: '3600' } }
        : RESPONSES[key]
    ));
    renderPage();
    search('45.33.32.156');
    await screen.findByText('Abuse Score: 100%');
    const expand = within(row('New Provider')).getByRole('button', { name: 'expand row' });
    await waitFor(() => expect(expand).toBeEnabled());
    fireEvent.click(expand);
    expect(await screen.findByText('Quota consumed. No API calls left.')).toBeInTheDocument();
    expect(screen.getByText('Retry after: 3600 seconds')).toBeInTheDocument();
  });

  it('expanding a provider row shows its detail view', async () => {
    renderPage();
    search('45.33.32.156');
    await screen.findByText('Abuse Score: 100%');
    fireEvent.click(within(row('AbuseIPDB')).getByRole('button', { name: 'expand row' }));
    expect(row('AbuseIPDB').nextSibling.textContent.length).toBeGreaterThan(0);
  });

  it('a domain lookup offers the Domain Finder pivot', async () => {
    renderPage();
    search('evil-domain.com');
    fireEvent.click(await screen.findByRole('button', { name: 'Enumerate in Domain Finder' }));
    expect(await screen.findByText('at /ioc-tools/domain-finder?q=evil-domain.com')).toBeInTheDocument();
  });

  it('prefills and runs from ?q=', async () => {
    renderPage('/ioc-tools/lookup?q=45.33.32.156');
    expect(await screen.findByText('Abuse Score: 100%')).toBeInTheDocument();
  });
});
