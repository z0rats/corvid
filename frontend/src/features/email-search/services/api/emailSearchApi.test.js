import api, { baseURL } from '../../../../core/services/baseApi';
import { getAccessToken } from '../../../../core/utils/accessToken';
import { emailSearchApi } from './emailSearchApi';

vi.mock('../../../../core/services/baseApi', () => ({
  default: { get: vi.fn(), post: vi.fn(), put: vi.fn(), delete: vi.fn() },
  baseURL: 'http://backend.test',
}));
vi.mock('../../../../core/utils/accessToken', () => ({ getAccessToken: vi.fn() }));

afterEach(() => {
  vi.clearAllMocks();
  vi.unstubAllGlobals();
});

describe('emailSearchApi.startScan', () => {
  it('opens an SSE POST stream with the bearer token and username payload', async () => {
    getAccessToken.mockReturnValue('tok123');
    const body = {};
    const fetchMock = vi.fn().mockResolvedValue({ ok: true, body });
    vi.stubGlobal('fetch', fetchMock);

    const result = await emailSearchApi.startScan('someuser');

    expect(fetchMock).toHaveBeenCalledWith(`${baseURL}/api/email-search/scan`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Accept': 'text/event-stream',
        'Authorization': 'Bearer tok123',
      },
      body: JSON.stringify({ username: 'someuser' }),
      signal: undefined,
    });
    expect(result).toBe(body);
  });

  it('throws when the response is not ok', async () => {
    getAccessToken.mockReturnValue('tok123');
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue({ ok: false, statusText: 'Forbidden' }));

    await expect(emailSearchApi.startScan('someuser')).rejects.toThrow('Server error: Forbidden');
  });
});

describe('emailSearchApi.cancelScan', () => {
  it('posts to the cancel endpoint for the given search id', async () => {
    api.post.mockResolvedValue({});

    await emailSearchApi.cancelScan('search-1');

    expect(api.post).toHaveBeenCalledWith('/api/email-search/runs/search-1/cancel');
  });
});

describe('emailSearchApi.listRuns', () => {
  it('requests paginated runs with default skip/limit', async () => {
    api.get.mockResolvedValue({ data: { items: [] } });

    const result = await emailSearchApi.listRuns();

    expect(api.get).toHaveBeenCalledWith('/api/email-search/runs', { params: { skip: 0, limit: 100 } });
    expect(result).toEqual({ items: [] });
  });
});

describe('emailSearchApi.getRun', () => {
  it('requests a single run by id', async () => {
    api.get.mockResolvedValue({ data: { id: 'search-1' } });

    const result = await emailSearchApi.getRun('search-1');

    expect(api.get).toHaveBeenCalledWith('/api/email-search/runs/search-1');
    expect(result).toEqual({ id: 'search-1' });
  });
});

describe('emailSearchApi.deleteRun', () => {
  it('deletes a run by id', async () => {
    api.delete.mockResolvedValue({});

    await emailSearchApi.deleteRun('search-1');

    expect(api.delete).toHaveBeenCalledWith('/api/email-search/runs/search-1');
  });
});

describe('emailSearchApi.getInfo', () => {
  it('requests checker info', async () => {
    api.get.mockResolvedValue({ data: { version: '1.0' } });

    const result = await emailSearchApi.getInfo();

    expect(api.get).toHaveBeenCalledWith('/api/email-search/info');
    expect(result).toEqual({ version: '1.0' });
  });
});

describe('emailSearchApi.checkUpdate', () => {
  it('posts to the check-update endpoint', async () => {
    api.post.mockResolvedValue({ data: { updateAvailable: false } });

    const result = await emailSearchApi.checkUpdate();

    expect(api.post).toHaveBeenCalledWith('/api/email-search/check-update');
    expect(result).toEqual({ updateAvailable: false });
  });
});

describe('emailSearchApi.getConfig', () => {
  it('requests the email-search settings', async () => {
    api.get.mockResolvedValue({ data: { smtpEnabled: false } });

    const result = await emailSearchApi.getConfig();

    expect(api.get).toHaveBeenCalledWith('/api/settings/email-search');
    expect(result).toEqual({ smtpEnabled: false });
  });
});

describe('emailSearchApi.updateConfig', () => {
  it('puts the updated config', async () => {
    api.put.mockResolvedValue({ data: { smtpEnabled: true } });

    const result = await emailSearchApi.updateConfig({ smtpEnabled: true });

    expect(api.put).toHaveBeenCalledWith('/api/settings/email-search', { smtpEnabled: true });
    expect(result).toEqual({ smtpEnabled: true });
  });
});
