import api from '../../../../core/services/baseApi';
import { steamReconApi } from './steamReconApi';

vi.mock('../../../../core/services/baseApi', () => ({
  default: { post: vi.fn(), get: vi.fn(), delete: vi.fn() },
  baseURL: 'http://localhost:8000',
}));
vi.mock('../../../../core/utils/accessToken', () => ({ getAccessToken: () => 'test-token' }));

afterEach(() => {
  vi.clearAllMocks();
  vi.unstubAllGlobals();
});

describe('steamReconApi.profile', () => {
  it('posts the target and returns the response body', async () => {
    api.post.mockResolvedValue({ data: { profile: { steamid64: '1' } } });

    const result = await steamReconApi.profile('robinwalker');

    expect(api.post).toHaveBeenCalledWith('/api/steam-recon/profile', { target: 'robinwalker' });
    expect(result).toEqual({ profile: { steamid64: '1' } });
  });
});

describe('steamReconApi.startScan', () => {
  it('posts snake_case fields and returns the response body stream', async () => {
    const body = new ReadableStream();
    const fetchMock = vi.fn().mockResolvedValue({ ok: true, body });
    vi.stubGlobal('fetch', fetchMock);

    const result = await steamReconApi.startScan({
      target: 'robinwalker',
      maxFriends: 50,
      includeCsReport: false,
    });

    expect(fetchMock).toHaveBeenCalledWith(
      'http://localhost:8000/api/steam-recon/scan',
      expect.objectContaining({
        method: 'POST',
        body: JSON.stringify({ target: 'robinwalker', max_friends: 50, include_cs_report: false }),
      }),
    );
    expect(result).toBe(body);
  });

  it('throws when the response is not ok', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue({ ok: false, statusText: 'Bad Request' }));

    await expect(
      steamReconApi.startScan({ target: 'x', maxFriends: 1, includeCsReport: true }),
    ).rejects.toThrow('Bad Request');
  });
});

describe('steamReconApi.cancelScan', () => {
  it('posts to the cancel endpoint', async () => {
    api.post.mockResolvedValue({});

    await steamReconApi.cancelScan(42);

    expect(api.post).toHaveBeenCalledWith('/api/steam-recon/history/42/cancel');
  });
});

describe('steamReconApi.listSearches', () => {
  it('passes skip/limit params', async () => {
    api.get.mockResolvedValue({ data: [] });

    await steamReconApi.listSearches(5, 10);

    expect(api.get).toHaveBeenCalledWith('/api/steam-recon/history', { params: { skip: 5, limit: 10 } });
  });
});

describe('steamReconApi.getSearch', () => {
  it('fetches a single search by id', async () => {
    api.get.mockResolvedValue({ data: { id: 1 } });

    const result = await steamReconApi.getSearch(1);

    expect(api.get).toHaveBeenCalledWith('/api/steam-recon/history/1');
    expect(result).toEqual({ id: 1 });
  });
});

describe('steamReconApi.deleteSearch', () => {
  it('deletes a search by id', async () => {
    api.delete.mockResolvedValue({});

    await steamReconApi.deleteSearch(1);

    expect(api.delete).toHaveBeenCalledWith('/api/steam-recon/history/1');
  });
});
