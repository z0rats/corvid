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
