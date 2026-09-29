import api, { baseURL } from '../../../../core/services/baseApi';
import { getAccessToken } from '../../../../core/utils/accessToken';
import { phoneSearchApi } from './phoneSearchApi';

vi.mock('../../../../core/services/baseApi', () => ({
  default: { get: vi.fn(), post: vi.fn(), put: vi.fn(), delete: vi.fn() },
  baseURL: 'http://backend.test',
}));
vi.mock('../../../../core/utils/accessToken', () => ({ getAccessToken: vi.fn() }));

afterEach(() => {
  vi.clearAllMocks();
  vi.unstubAllGlobals();
});

describe('phoneSearchApi.startScan', () => {
  it('opens an SSE POST stream with the bearer token and phone number payload', async () => {
    getAccessToken.mockReturnValue('tok123');
    const body = {};
    const fetchMock = vi.fn().mockResolvedValue({ ok: true, body });
    vi.stubGlobal('fetch', fetchMock);

    const result = await phoneSearchApi.startScan('+15551234567');

    expect(fetchMock).toHaveBeenCalledWith(`${baseURL}/api/phone-search/scan`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Accept': 'text/event-stream',
        'Authorization': 'Bearer tok123',
      },
      body: JSON.stringify({ phone_number: '+15551234567' }),
      signal: undefined,
    });
    expect(result).toBe(body);
  });

  it('throws when the response is not ok', async () => {
    getAccessToken.mockReturnValue('tok123');
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue({ ok: false, statusText: 'Forbidden' }));

    await expect(phoneSearchApi.startScan('+15551234567')).rejects.toThrow('Server error: Forbidden');
  });
});

describe('phoneSearchApi.cancelScan', () => {
  it('posts to the cancel endpoint for the given search id', async () => {
    api.post.mockResolvedValue({});

    await phoneSearchApi.cancelScan('search-1');

    expect(api.post).toHaveBeenCalledWith('/api/phone-search/runs/search-1/cancel');
  });
});

describe('phoneSearchApi.listRuns', () => {
  it('requests paginated runs with default skip/limit', async () => {
    api.get.mockResolvedValue({ data: { items: [] } });

    const result = await phoneSearchApi.listRuns();

    expect(api.get).toHaveBeenCalledWith('/api/phone-search/runs', { params: { skip: 0, limit: 100 } });
    expect(result).toEqual({ items: [] });
  });
});

describe('phoneSearchApi.getRun', () => {
  it('requests a single run by id', async () => {
    api.get.mockResolvedValue({ data: { id: 'search-1' } });

    const result = await phoneSearchApi.getRun('search-1');

    expect(api.get).toHaveBeenCalledWith('/api/phone-search/runs/search-1');
    expect(result).toEqual({ id: 'search-1' });
  });
});

describe('phoneSearchApi.deleteRun', () => {
  it('deletes a run by id', async () => {
    api.delete.mockResolvedValue({});

    await phoneSearchApi.deleteRun('search-1');

    expect(api.delete).toHaveBeenCalledWith('/api/phone-search/runs/search-1');
  });
});

describe('phoneSearchApi.getInfo', () => {
  it('requests checker info', async () => {
    api.get.mockResolvedValue({ data: { provider_count: 3 } });

    const result = await phoneSearchApi.getInfo();

    expect(api.get).toHaveBeenCalledWith('/api/phone-search/info');
    expect(result).toEqual({ provider_count: 3 });
  });
});

describe('phoneSearchApi.getConfig', () => {
  it('requests the phone-search settings', async () => {
    api.get.mockResolvedValue({ data: { timeout_seconds: 10 } });

    const result = await phoneSearchApi.getConfig();

    expect(api.get).toHaveBeenCalledWith('/api/settings/phone-search');
    expect(result).toEqual({ timeout_seconds: 10 });
  });
});

describe('phoneSearchApi.updateConfig', () => {
  it('puts the updated config', async () => {
    api.put.mockResolvedValue({ data: { timeout_seconds: 20 } });

    const result = await phoneSearchApi.updateConfig({ timeout_seconds: 20 });

    expect(api.put).toHaveBeenCalledWith('/api/settings/phone-search', { timeout_seconds: 20 });
    expect(result).toEqual({ timeout_seconds: 20 });
  });
});
