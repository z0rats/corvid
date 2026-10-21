import { render, screen, fireEvent, within, waitFor } from '@testing-library/react';
import { MemoryRouter } from 'react-router';
import { Provider, createStore } from 'jotai';
import { ThemeProvider } from '@mui/material/styles';
import { lightTheme } from '../../../../core/config/theme';
import BulkLookup from './BulkLookup';
import { iocLookupApi } from '../../shared/services/api/iocLookupApi';

vi.mock('../../shared/services/api/iocLookupApi', () => ({
  iocLookupApi: {
    fetchServiceDefinitions: vi.fn(),
    fetchBulkLookupSettings: vi.fn(),
    updateBulkLookupSetting: vi.fn(),
    bulkLookup: vi.fn(),
  },
}));

const DEFINITIONS = {
  abuseipdb: { name: 'AbuseIPDB', supportedIocTypes: ['IPv4'], isAvailable: true, requiredKeys: ['abuseipdb'] },
  virustotal: { name: 'VirusTotal', supportedIocTypes: ['IPv4', 'Domain'], isAvailable: true, requiredKeys: ['virustotal'] },
};

function sseStream(events) {
  const encoder = new TextEncoder();
  const frames = events.map((e) => `data: ${JSON.stringify(e)}\n\n`);
  let i = 0;
  return new ReadableStream({
    pull(controller) {
      if (i < frames.length) controller.enqueue(encoder.encode(frames[i++]));
      else controller.close();
    },
  });
}

function renderPage() {
  return render(
    <ThemeProvider theme={lightTheme}>
      <Provider store={createStore()}>
        <MemoryRouter initialEntries={['/ioc-tools/bulk']}><BulkLookup /></MemoryRouter>
      </Provider>
    </ThemeProvider>,
  );
}

beforeEach(() => {
  iocLookupApi.fetchServiceDefinitions.mockResolvedValue(DEFINITIONS);
  iocLookupApi.fetchBulkLookupSettings.mockResolvedValue({ abuseipdb: true, virustotal: false });
  iocLookupApi.updateBulkLookupSetting.mockResolvedValue({});
});
afterEach(() => vi.clearAllMocks());

const input = () => screen.getByLabelText(/Enter IOCs/i);

describe('BulkLookup flow', () => {
  it('lists bulk settings per service and toggles one', async () => {
    renderPage();
    fireEvent.click(await screen.findByText('Bulk IOC Lookup Settings'));
    const vt = await screen.findByRole('switch', { name: 'VirusTotal' });
    expect(vt).not.toBeChecked();
    expect(screen.getByRole('switch', { name: 'AbuseIPDB' })).toBeChecked();
    fireEvent.click(vt);
    await waitFor(() => expect(iocLookupApi.updateBulkLookupSetting).toHaveBeenCalledWith('virustotal', true));
  });

  it('streams results per IOC and colours the card by the worst verdict', async () => {
    iocLookupApi.bulkLookup.mockResolvedValue(sseStream([
      { ioc: '45.33.32.156', service: 'abuseipdb', data: { data: { abuseConfidenceScore: 100 } } },
      { ioc: '8.8.8.8', service: 'abuseipdb', data: { data: { abuseConfidenceScore: 0 } } },
    ]));
    renderPage();
    await screen.findByText('Bulk IOC Lookup Settings');
    fireEvent.change(input(), { target: { value: '45.33.32.156\n8.8.8.8\n45.33.32.156' } });
    fireEvent.click(screen.getByRole('button', { name: 'Analyze IOCs' }));

    await waitFor(() => expect(iocLookupApi.bulkLookup).toHaveBeenCalledWith(
      ['45.33.32.156', '8.8.8.8'], ['abuseipdb'], expect.anything(),
    ));
    expect(await screen.findByRole('tab', { name: 'IPV4 (2)' })).toBeInTheDocument();
    const card = screen.getByText('45.33.32.156').closest('.MuiCard-root');
    fireEvent.click(within(card).getByRole('button', { name: 'show more' }));
    expect(await within(card).findByText('Abuse Score: 100%')).toBeInTheDocument();
    fireEvent.click(within(card).getByRole('button', { name: 'expand row' }));
  });

  it('submit is disabled without input or without enabled services', async () => {
    iocLookupApi.fetchBulkLookupSettings.mockResolvedValue({ abuseipdb: false, virustotal: false });
    renderPage();
    await screen.findByText('Bulk IOC Lookup Settings');
    fireEvent.change(input(), { target: { value: '8.8.8.8' } });
    expect(screen.getByRole('button', { name: 'Analyze IOCs' })).toBeDisabled();
    expect(screen.getByText('Enable at least one service in settings above')).toBeInTheDocument();
  });

  it('a broken stream is reported', async () => {
    iocLookupApi.bulkLookup.mockRejectedValue(new Error('502 Bad Gateway'));
    renderPage();
    await screen.findByText('Bulk IOC Lookup Settings');
    fireEvent.change(input(), { target: { value: '8.8.8.8' } });
    fireEvent.click(screen.getByRole('button', { name: 'Analyze IOCs' }));
    expect(await screen.findByText('Failed to connect or stream results: 502 Bad Gateway')).toBeInTheDocument();
  });

  it('a dropped file of the wrong type is rejected', async () => {
    renderPage();
    await screen.findByText('Bulk IOC Lookup Settings');
    const file = new File(['x'], 'malware.exe', { type: 'application/x-msdownload' });
    fireEvent.drop(screen.getByText('Drop files here'), { dataTransfer: { files: [file] } });
    expect(await screen.findByText('Invalid file type. Please drop a CSV, MD, or TXT file.')).toBeInTheDocument();
  });

  it('a dropped text file fills the input', async () => {
    renderPage();
    await screen.findByText('Bulk IOC Lookup Settings');
    const file = new File(['1.1.1.1\n2.2.2.2'], 'iocs.txt', { type: 'text/plain' });
    fireEvent.drop(screen.getByText('Drop files here'), { dataTransfer: { files: [file] } });
    await waitFor(() => expect(input().value).toBe('1.1.1.1\n2.2.2.2'));
  });
});
