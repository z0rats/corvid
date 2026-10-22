import { cloneElement } from 'react';
import { render, screen, fireEvent, within, waitFor } from '@testing-library/react';
import { MemoryRouter } from 'react-router';
import { Provider, createStore } from 'jotai';
import { ThemeProvider } from '@mui/material/styles';
import { lightTheme } from '../../../core/config/theme';
import DomainMonitoring from './DomainMonitoring';
import api from '../../../core/services/baseApi';

vi.mock('recharts', async (importOriginal) => {
  const actual = await importOriginal();
  return {
    ...actual,
    ResponsiveContainer: ({ children }) => <div>{cloneElement(children, { width: 800, height: 300 })}</div>,
  };
});
vi.mock('../../../core/services/baseApi', () => ({ default: { get: vi.fn(), post: vi.fn() } }));

const URLSCAN_ROW = {
  task: { domain: 'login-example.com', time: '2026-10-01T10:00:00Z', uuid: 'abc-123' },
  page: { country: 'US', status: 200, ip: '93.184.216.34', url: 'https://login-example.com/', server: 'nginx', asnname: 'EDGECAST' },
  result: 'https://urlscan.io/result/abc-123/',
};

const PANELS = {
  whois: { registrar: 'NameCheap, Inc.', creation_date: '2020-01-01', nameservers: ['ns1.example.net'], statuses: ['clientTransferProhibited'], rdap_server: 'rdap.example' },
  dns: { records: { A: ['93.184.216.34'], MX: ['mx.example.com'] }, reverse_dns: { '93.184.216.34': ['edge.example.net'] } },
  'ct-subdomains': {
    subdomains: ['mail.example.com', 'vpn.example.com'],
    sources: [{ name: 'crt.sh', ok: true, subdomain_count: 2, certificate_count: 7, truncated: false }],
    total_certificates: 7,
  },
  'hackertarget-subdomains': { subdomains: [], total_hosts: 0 },
  'rapiddns-subdomains': { subdomains: ['dev.example.com'], total_records: 1 },
  wayback: { snapshots: [], total_snapshots: 0 },
  'temporal-analysis': { events: [], sources_failed: [] },
  'ssl-info': { issuer: "CN=R3,O=Let's Encrypt", subject: 'CN=example.com', days_until_expiry: 40, is_expired: false, hostname_matches: true, tls_version: 'TLSv1.3' },
  'security-headers': { present_headers: { 'strict-transport-security': 'max-age=1' }, missing_headers: ['content-security-policy'], hsts: { max_age: 1, include_subdomains: false, preload: false } },
  dnssec: { dnssec_enabled: false },
  blocklist: { results: [], flagged_count: 0 },
  'subfinder-subdomains': { subdomains: ['api.example.com'], total_records: 1 },
  'host-probe': { reachable: true, results: [{ url: 'https://example.com', scheme: 'https', status_code: 200, title: 'Example', technologies: ['nginx'] }] },
  'site-crawl': { pages: [{ url: 'https://example.com/', status_code: 200, title: 'Home' }], total_pages_crawled: 1, iocs: { statistics: { total_unique_iocs: 0 } }, errors: [] },
};

function routeGet(overrides = {}) {
  const panels = { ...PANELS, ...overrides };
  api.get.mockImplementation(async (url) => {
    if (url.startsWith('/api/domain/lookup/')) return { data: { results: [URLSCAN_ROW] } };
    const [, , , path] = url.split('/');
    if (panels[path] instanceof Error) throw panels[path];
    if (path in panels) return { data: panels[path] };
    throw Object.assign(new Error('not mocked'), { response: { data: { detail: `no mock for ${path}` } } });
  });
}

function renderPage(path = '/ioc-tools/domain-finder') {
  return render(
    <ThemeProvider theme={lightTheme}>
      <Provider store={createStore()}>
        <MemoryRouter initialEntries={[path]}><DomainMonitoring /></MemoryRouter>
      </Provider>
    </ThemeProvider>,
  );
}

function search(value) {
  fireEvent.change(screen.getByPlaceholderText('Please enter a domain pattern to search for...'), { target: { value } });
  fireEvent.click(screen.getByRole('button', { name: 'Search' }));
}

beforeEach(() => routeGet());
afterEach(() => vi.clearAllMocks());

describe('DomainMonitoring', () => {
  it('rejects an empty search', () => {
    renderPage();
    search('   ');
    expect(screen.getByText('Please enter a domain pattern to search for')).toBeInTheDocument();
    expect(api.get).not.toHaveBeenCalled();
  });

  it('runs the auto panels and the urlscan search for an exact domain', async () => {
    renderPage();
    search('example.com');
    expect(await screen.findByText('NameCheap, Inc.')).toBeInTheDocument();
    expect(await screen.findByText('mail.example.com')).toBeInTheDocument();
    expect(await screen.findByText('edge.example.net')).toBeInTheDocument();
    expect(await screen.findByText('login-example.com')).toBeInTheDocument();
    const requested = api.get.mock.calls.map(([url]) => url);
    expect(requested).toContain('/api/domain/whois/example.com');
    expect(requested).toContain('/api/domain/lookup/example.com');
    // slow/active panels wait for an explicit click
    expect(requested).not.toContain('/api/domain/subfinder-subdomains/example.com');
    expect(requested).not.toContain('/api/domain/host-probe/example.com');
    expect(requested).not.toContain('/api/domain/site-crawl/example.com');
  });

  it('active panels run on click', async () => {
    renderPage();
    search('example.com');
    fireEvent.click(await screen.findByRole('button', { name: 'Run subfinder' }));
    expect(await screen.findByText('api.example.com')).toBeInTheDocument();
    fireEvent.click(screen.getByRole('button', { name: 'Probe host' }));
    expect(await screen.findByText('Example')).toBeInTheDocument();
    fireEvent.click(screen.getByRole('button', { name: 'Start crawl' }));
    expect(await screen.findByText('https://example.com/')).toBeInTheDocument();
    expect(screen.getByText('No IOCs found across the crawled pages.')).toBeInTheDocument();
  });

  it('clicking a discovered subdomain pivots the whole page to it', async () => {
    renderPage();
    search('example.com');
    fireEvent.click(await screen.findByText('vpn.example.com'));
    await waitFor(() => expect(api.get).toHaveBeenCalledWith('/api/domain/whois/vpn.example.com', expect.anything()));
  });

  it('a search pattern skips exact-domain panels', async () => {
    renderPage();
    search('*.example.com');
    expect(await screen.findByText("WHOIS lookup requires an exact domain and doesn't support search patterns.")).toBeInTheDocument();
    const requested = api.get.mock.calls.map(([url]) => url);
    expect(requested.filter((u) => u.startsWith('/api/domain/whois/'))).toEqual([]);
    expect(requested).toContain('/api/domain/lookup/*.example.com');
  });

  it('panel errors and a missing DNSDumpster key are shown in place', async () => {
    routeGet({
      whois: Object.assign(new Error('x'), { response: { data: { detail: 'RDAP server timed out' } } }),
      dnsdumpster: Object.assign(new Error('x'), { response: { data: { detail: 'no key', error_code: 'DNSDUMPSTER_NOT_CONFIGURED' } } }),
    });
    renderPage();
    search('example.com');
    expect(await screen.findByText(/RDAP server timed out/)).toBeInTheDocument();
    expect(await screen.findByText('Add a free DNSDumpster API key in Settings to enable this panel.')).toBeInTheDocument();
    expect(screen.getByRole('link', { name: 'Add API key' })).toHaveAttribute('href', expect.stringContaining('dnsdumpster'));
  });

  it('expands an urlscan result row into its details', async () => {
    renderPage();
    search('example.com');
    const domainCell = await screen.findByText('login-example.com');
    fireEvent.click(within(domainCell.closest('tr')).getByRole('button', { name: 'expand row' }));
    expect(await screen.findByText(/EDGECAST/)).toBeInTheDocument();
    expect(screen.getAllByText(/93\.184\.216\.34/).length).toBeGreaterThan(0);
  });

  it('prefills and searches from ?q=', async () => {
    renderPage('/ioc-tools/domain-finder?q=example.com');
    expect(await screen.findByText('NameCheap, Inc.')).toBeInTheDocument();
  });

  it('renders history, archive, DNSDumpster and blocklist data', async () => {
    routeGet({
      wayback: {
        snapshots: [{ timestamp: '20240102030405', original_url: 'https://example.com/login', snapshot_url: 'https://web.archive.org/web/20240102030405/https://example.com/login' }],
        total_snapshots: 1, first_capture: '20240102030405', last_capture: '20240102030405',
      },
      'temporal-analysis': {
        events: [
          { date: '2020-01-01', source: 'whois', category: 'server', label: 'Domain registered' },
          { date: '2024-01-02', source: 'wayback', category: 'page', label: 'First archived' },
        ],
        sources_failed: ['schema_org'],
      },
      dnsdumpster: {
        a: [{ host: 'example.com', ips: [{ ip: '93.184.216.34', asn: '15133', asn_name: 'EDGECAST', ptr: 'edge.example.net', country_code: 'US' }] }],
        ns: [], mx: [], cname: [], txt: ['v=spf1 -all'], total_a_records: 1,
      },
      blocklist: { results: [{ provider: 'Quad9', blocked: true }, { provider: 'Cloudflare', blocked: false }], flagged_count: 1 },
    });
    renderPage();
    search('example.com');
    expect(await screen.findByText('Domain registered')).toBeInTheDocument();
    expect(screen.getByText('Could not fetch: Schema.org')).toBeInTheDocument();
    expect(await screen.findByText('Flagged by 1 provider(s)')).toBeInTheDocument();
    expect(await screen.findByText('v=spf1 -all')).toBeInTheDocument();
    expect(screen.getByText(/AS15133 · EDGECAST/)).toBeInTheDocument();
    await screen.findByText('https://example.com/login');
    expect(screen.getByTitle('Open this snapshot on web.archive.org')).toHaveAttribute('href', expect.stringMatching(/^https:\/\/web\.archive\.org\//));

    fireEvent.change(screen.getByPlaceholderText('Narrow to a page, e.g. /login (optional)'), { target: { value: '/login' } });
    fireEvent.keyDown(screen.getByPlaceholderText('Narrow to a page, e.g. /login (optional)'), { key: 'Enter' });
    await waitFor(() => expect(api.get).toHaveBeenCalledWith('/api/domain/wayback/example.com', expect.objectContaining({ params: { path: '/login' } })));
  });
});
