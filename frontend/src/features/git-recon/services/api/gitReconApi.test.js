import api, { baseURL } from '../../../../core/services/baseApi';
import { getAccessToken } from '../../../../core/utils/accessToken';
import { gitReconApi } from './gitReconApi';

vi.mock('../../../../core/services/baseApi', () => ({
  default: { get: vi.fn(), post: vi.fn(), delete: vi.fn() },
  baseURL: 'http://backend.test',
}));
vi.mock('../../../../core/utils/accessToken', () => ({ getAccessToken: vi.fn() }));

afterEach(() => {
  vi.clearAllMocks();
  vi.unstubAllGlobals();
});

describe('gitReconApi.startScan', () => {
  it('opens an SSE POST stream with the bearer token and the given payload', async () => {
    getAccessToken.mockReturnValue('tok123');
    const body = {};
    const fetchMock = vi.fn().mockResolvedValue({ ok: true, body });
    vi.stubGlobal('fetch', fetchMock);
    const payload = { mode: 'search', query: 'octocat' };

    const result = await gitReconApi.startScan(payload);

    expect(fetchMock).toHaveBeenCalledWith(`${baseURL}/api/git-recon/scan`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Accept': 'text/event-stream',
        'Authorization': 'Bearer tok123',
      },
      body: JSON.stringify(payload),
      signal: undefined,
    });
    expect(result).toBe(body);
  });

  it('throws when the response has no body', async () => {
    getAccessToken.mockReturnValue('tok123');
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue({ ok: true, body: null }));

    await expect(gitReconApi.startScan({ mode: 'search' })).rejects.toThrow('Server error');
  });
});

describe('gitReconApi.cancelScan', () => {
  it('posts to the cancel endpoint for the given search id', async () => {
    api.post.mockResolvedValue({});

    await gitReconApi.cancelScan('search-1');

    expect(api.post).toHaveBeenCalledWith('/api/git-recon/history/search-1/cancel');
  });
});

describe('gitReconApi.listHistory', () => {
  it('requests paginated history with default skip/limit', async () => {
    api.get.mockResolvedValue({ data: { items: [] } });

    const result = await gitReconApi.listHistory();

    expect(api.get).toHaveBeenCalledWith('/api/git-recon/history', { params: { skip: 0, limit: 100 } });
    expect(result).toEqual({ items: [] });
  });
});

describe('gitReconApi.getHistory', () => {
  it('requests a single history entry by id', async () => {
    api.get.mockResolvedValue({ data: { id: 'search-1' } });

    const result = await gitReconApi.getHistory('search-1');

    expect(api.get).toHaveBeenCalledWith('/api/git-recon/history/search-1');
    expect(result).toEqual({ id: 'search-1' });
  });
});

describe('gitReconApi.deleteHistory', () => {
  it('deletes a history entry by id', async () => {
    api.delete.mockResolvedValue({});

    await gitReconApi.deleteHistory('search-1');

    expect(api.delete).toHaveBeenCalledWith('/api/git-recon/history/search-1');
  });
});
