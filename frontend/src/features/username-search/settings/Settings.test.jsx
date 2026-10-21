import { render, screen, fireEvent, within, waitFor } from '@testing-library/react';
import Settings from './Settings';
import { usernameSearchApi } from '../services/api/usernameSearchApi';

vi.mock('../services/api/usernameSearchApi', () => ({
  usernameSearchApi: {
    getConfig: vi.fn(), updateConfig: vi.fn(), refreshDb: vi.fn(), checkMaigretUpdate: vi.fn(),
    getSocialAnalyzerConfig: vi.fn(), updateSocialAnalyzerConfig: vi.fn(), checkSocialAnalyzerUpdate: vi.fn(),
  },
}));

const CONFIG = {
  timeout_seconds: 30, max_concurrency: 50, top_sites_count: 500, proxy_url: '',
  auto_update_db_enabled: false, auto_update_interval_hours: 24, db_site_count: 3100, db_last_updated_at: null,
};
const SA_CONFIG = { timeout_seconds: 1, top_sites_count: 100 };

async function setup() {
  usernameSearchApi.getConfig.mockResolvedValue(CONFIG);
  usernameSearchApi.getSocialAnalyzerConfig.mockResolvedValue(SA_CONFIG);
  usernameSearchApi.updateConfig.mockImplementation(async (c) => c);
  usernameSearchApi.updateSocialAnalyzerConfig.mockImplementation(async (c) => c);
  render(<Settings />);
  await screen.findByText('Username Search Settings');
}

const maigretCard = () => screen.getByText('Username Search Settings').closest('.MuiCard-root');
const saCard = () => screen.getByText('Social Analyzer Settings').closest('.MuiCard-root');

function commit(input, value) {
  fireEvent.focus(input);
  fireEvent.change(input, { target: { value } });
  fireEvent.blur(input);
}

afterEach(() => vi.clearAllMocks());

describe('username-search Settings', () => {
  it('typing alone saves nothing; blur saves the field once, as a number', async () => {
    await setup();
    const input = within(maigretCard()).getByLabelText('Max concurrency');
    fireEvent.focus(input);
    fireEvent.change(input, { target: { value: '1' } });
    fireEvent.change(input, { target: { value: '10' } });
    expect(usernameSearchApi.updateConfig).not.toHaveBeenCalled();
    fireEvent.blur(input);
    await waitFor(() => expect(usernameSearchApi.updateConfig).toHaveBeenCalledTimes(1));
    expect(usernameSearchApi.updateConfig).toHaveBeenCalledWith(expect.objectContaining({ max_concurrency: 10 }));
  });

  it('saves maigret fields as numbers', async () => {
    await setup();
    commit(within(maigretCard()).getByLabelText('Timeout (seconds)'), '45');
    expect(await screen.findByText('Settings updated successfully')).toBeInTheDocument();
    expect(usernameSearchApi.updateConfig).toHaveBeenLastCalledWith(expect.objectContaining({ timeout_seconds: 45 }));
    commit(within(maigretCard()).getByLabelText('Proxy URL'), 'socks5://127.0.0.1:9050');
    await waitFor(() => expect(usernameSearchApi.updateConfig).toHaveBeenLastCalledWith(expect.objectContaining({ proxy_url: 'socks5://127.0.0.1:9050' })));
  });

  it('enabling DB auto-update reveals the interval field', async () => {
    await setup();
    expect(screen.queryByLabelText('Check interval (hours)')).toBeNull();
    fireEvent.click(within(maigretCard()).getByRole('switch'));
    expect(await screen.findByLabelText('Check interval (hours)')).toBeInTheDocument();
    expect(screen.getByText('3100 sites (bundled database, never checked for updates)')).toBeInTheDocument();
  });

  it('refreshes the site DB on demand and surfaces backend errors', async () => {
    await setup();
    usernameSearchApi.refreshDb.mockResolvedValueOnce({});
    fireEvent.click(screen.getByRole('button', { name: 'Check for update now' }));
    expect(await screen.findByText('Site database refresh complete')).toBeInTheDocument();

    usernameSearchApi.refreshDb.mockRejectedValueOnce({ response: { data: { detail: 'GitHub rate limited' } } });
    fireEvent.click(screen.getByRole('button', { name: 'Check for update now' }));
    expect(await screen.findByText('GitHub rate limited')).toBeInTheDocument();
  });

  it('PyPI checks show the latest version for each tool', async () => {
    usernameSearchApi.checkMaigretUpdate.mockResolvedValue({ latest_version: '0.5.0' });
    usernameSearchApi.checkSocialAnalyzerUpdate.mockResolvedValue({ latest_version: '1.2.3' });
    await setup();
    expect(within(maigretCard()).getByText('PyPI has not been checked for a newer version yet')).toBeInTheDocument();
    fireEvent.click(within(maigretCard()).getByRole('button', { name: 'Check PyPI for updates' }));
    expect(await within(maigretCard()).findByText(/Latest available on PyPI: v0\.5\.0/)).toBeInTheDocument();
    fireEvent.click(within(saCard()).getByRole('button', { name: 'Check PyPI for updates' }));
    expect(await within(saCard()).findByText(/Latest available on PyPI: v1\.2\.3/)).toBeInTheDocument();
  });

  it('saves social-analyzer fields separately', async () => {
    await setup();
    commit(within(saCard()).getByLabelText('Delay between requests (seconds)'), '2');
    await waitFor(() => expect(usernameSearchApi.updateSocialAnalyzerConfig).toHaveBeenLastCalledWith(expect.objectContaining({ timeout_seconds: 2 })));
    expect(usernameSearchApi.updateConfig).not.toHaveBeenCalled();
  });
});
