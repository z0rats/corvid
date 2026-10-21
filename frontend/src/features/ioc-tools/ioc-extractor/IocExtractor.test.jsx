import { render, screen, fireEvent, within, waitFor } from '@testing-library/react';
import { MemoryRouter } from 'react-router';
import { Provider, createStore } from 'jotai';
import { ThemeProvider } from '@mui/material/styles';
import { lightTheme } from '../../../core/config/theme';
import IocExtractor from './IocExtractor';
import { extractorApi } from '../shared/services/api/extractorApi';
import { iocLookupApi } from '../shared/services/api/iocLookupApi';

vi.mock('../shared/services/api/extractorApi', () => ({ extractorApi: { extractFromFile: vi.fn(), extractFromText: vi.fn() } }));
vi.mock('../shared/services/api/iocLookupApi', () => ({
  iocLookupApi: { fetchServiceDefinitions: vi.fn(), lookupSingleService: vi.fn(), fetchNewsfeedMentions: vi.fn() },
}));

const ips = Array.from({ length: 12 }, (_, i) => `10.0.0.${i + 1}`);
const RESULT = {
  domains: ['evil-domain.com'],
  ips,
  urls: [],
  emails: [],
  md5: ['d41d8cd98f00b204e9800998ecf8427e'],
  sha1: [], sha256: [], cves: [], paths: [],
  statistics: { total_unique_iocs: 14, domains: 1, ips: 12, md5: 1, duplicates_removed: { ips: 3 } },
};

function renderPage() {
  return render(
    <ThemeProvider theme={lightTheme}>
      <Provider store={createStore()}><MemoryRouter><IocExtractor /></MemoryRouter></Provider>
    </ThemeProvider>,
  );
}

async function upload(container, name = 'report.txt') {
  const file = new File(['C2 at 10.0.0.1'], name, { type: 'text/plain' });
  fireEvent.change(container.querySelector('input[type="file"]'), { target: { files: [file] } });
  await screen.findByText(new RegExp(name));
  fireEvent.click(screen.getByRole('button', { name: 'Extract' }));
  return file;
}

beforeEach(() => {
  Object.assign(navigator, { clipboard: { writeText: vi.fn().mockResolvedValue(undefined) } });
  iocLookupApi.fetchServiceDefinitions.mockResolvedValue({
    abuseipdb: { name: 'AbuseIPDB', supportedIocTypes: ['IPv4'], isAvailable: true },
  });
  iocLookupApi.lookupSingleService.mockResolvedValue({ data: { data: { abuseConfidenceScore: 0 } } });
  iocLookupApi.fetchNewsfeedMentions.mockResolvedValue({ count: 0, articles: [] });
});
afterEach(() => vi.clearAllMocks());

describe('IocExtractor', () => {
  it('shows the welcome screen until a file is extracted', () => {
    renderPage();
    expect(screen.getByText('IOC Extractor')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Extract' })).toBeInTheDocument();
  });

  it('extracts from an uploaded file and groups results by type', async () => {
    extractorApi.extractFromFile.mockResolvedValue(RESULT);
    const { container } = renderPage();
    const file = await upload(container);
    expect(await screen.findByText('IOC extraction completed successfully')).toBeInTheDocument();
    expect(extractorApi.extractFromFile).toHaveBeenCalledWith(file, expect.any(Function));
    expect(screen.getByText('IP addresses (12)')).toBeInTheDocument();
    expect(screen.getByText('Domains (1)')).toBeInTheDocument();
  });

  it('paginates a long category and copies all of it', async () => {
    extractorApi.extractFromFile.mockResolvedValue(RESULT);
    const { container } = renderPage();
    await upload(container);
    const summary = await screen.findByText('IP addresses (12)');
    fireEvent.click(summary);
    const section = summary.closest('.MuiAccordion-root');
    expect(within(section).getByText('10.0.0.1')).toBeInTheDocument();
    expect(within(section).queryByText('10.0.0.11')).toBeNull(); // 10 per page
    fireEvent.click(within(section).getByRole('button', { name: /next page/i }));
    expect(within(section).getByText('10.0.0.11')).toBeInTheDocument();

    fireEvent.click(within(section).getByRole('button', { name: 'Copy all' }));
    await waitFor(() => expect(navigator.clipboard.writeText).toHaveBeenCalledWith(ips.join('\n')));
  });

  it('Analyze opens a lookup of that IOC across providers', async () => {
    extractorApi.extractFromFile.mockResolvedValue(RESULT);
    const { container } = renderPage();
    await upload(container);
    const summary = await screen.findByText('IP addresses (12)');
    fireEvent.click(summary);
    const section = summary.closest('.MuiAccordion-root');
    fireEvent.click(within(section).getAllByRole('button', { name: 'Analyze' })[0]);
    expect(await screen.findByText('Abuse Score: 0%')).toBeInTheDocument();
    expect(iocLookupApi.lookupSingleService).toHaveBeenCalledWith('abuseipdb', '10.0.0.1', 'IPv4', expect.anything());
  });

  it('reports a failed extraction', async () => {
    extractorApi.extractFromFile.mockRejectedValue(new Error('Unsupported file type'));
    const { container } = renderPage();
    await upload(container);
    expect(await screen.findByText(/Unsupported file type|Failed to extract/)).toBeInTheDocument();
  });
});
