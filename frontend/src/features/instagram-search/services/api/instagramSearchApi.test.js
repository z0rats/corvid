import api, { baseURL } from '../../../../core/services/baseApi';
import { getAccessToken } from '../../../../core/utils/accessToken';
import { instagramSearchApi } from './instagramSearchApi';

vi.mock('../../../../core/services/baseApi', () => ({
  default: { get: vi.fn(), post: vi.fn(), delete: vi.fn() },
  baseURL: 'http://backend.test',
}));
vi.mock('../../../../core/utils/accessToken', () => ({ getAccessToken: vi.fn() }));

afterEach(() => {
  vi.clearAllMocks();
  vi.unstubAllGlobals();
});

describe('instagramSearchApi.lookupProfile', () => {
  it('posts the username', async () => {
    api.post.mockResolvedValue({ data: { username: 'someuser' } });

    const result = await instagramSearchApi.lookupProfile('someuser');

    expect(api.post).toHaveBeenCalledWith('/api/instagram-search/profile', { username: 'someuser' });
    expect(result).toEqual({ username: 'someuser' });
  });
});

describe('instagramSearchApi.getHealth', () => {
  it('gets the health endpoint', async () => {
    api.get.mockResolvedValue({ data: { installed_version: '4.15.3', session_configured: false } });

    const result = await instagramSearchApi.getHealth();

    expect(api.get).toHaveBeenCalledWith('/api/instagram-search/health');
    expect(result).toEqual({ installed_version: '4.15.3', session_configured: false });
  });
});

describe('instagramSearchApi.startScan', () => {
  it('opens an SSE POST stream with the bearer token and the scan payload', async () => {
    getAccessToken.mockReturnValue('tok123');
    const body = {};
    const fetchMock = vi.fn().mockResolvedValue({ ok: true, body });
    vi.stubGlobal('fetch', fetchMock);

    const result = await instagramSearchApi.startScan({ username: 'someuser', scanType: 'posts' });

    expect(fetchMock).toHaveBeenCalledWith(`${baseURL}/api/instagram-search/scan`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Accept': 'text/event-stream',
        'Authorization': 'Bearer tok123',
      },
      body: JSON.stringify({ username: 'someuser', scan_type: 'posts' }),
      signal: undefined,
    });
    expect(result).toBe(body);
  });

  it('throws when the response has no body', async () => {
    getAccessToken.mockReturnValue('tok123');
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue({ ok: true, body: null }));

    await expect(
      instagramSearchApi.startScan({ username: 'someuser', scanType: 'posts' }),
    ).rejects.toThrow('Server error');
  });
});

describe('instagramSearchApi.cancelScan', () => {
  it('posts to the cancel endpoint for the given search id', async () => {
    api.post.mockResolvedValue({});

    await instagramSearchApi.cancelScan(1);

    expect(api.post).toHaveBeenCalledWith('/api/instagram-search/history/1/cancel');
  });
});

describe('instagramSearchApi.listHistory', () => {
  it('requests paginated history with default skip/limit', async () => {
    api.get.mockResolvedValue({ data: [] });

    const result = await instagramSearchApi.listHistory();

    expect(api.get).toHaveBeenCalledWith('/api/instagram-search/history', {
      params: { skip: 0, limit: 100 },
    });
    expect(result).toEqual([]);
  });
});

describe('instagramSearchApi.getHistory', () => {
  it('requests a single history entry by id', async () => {
    api.get.mockResolvedValue({ data: { id: 1 } });

    const result = await instagramSearchApi.getHistory(1);

    expect(api.get).toHaveBeenCalledWith('/api/instagram-search/history/1');
    expect(result).toEqual({ id: 1 });
  });
});

describe('instagramSearchApi.deleteHistory', () => {
  it('deletes a history entry by id', async () => {
    api.delete.mockResolvedValue({});

    await instagramSearchApi.deleteHistory(1);

    expect(api.delete).toHaveBeenCalledWith('/api/instagram-search/history/1');
  });
});
