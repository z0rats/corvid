import api from '../../../../core/services/baseApi';
import { redditSearchApi } from './redditSearchApi';

vi.mock('../../../../core/services/baseApi', () => ({
  default: { get: vi.fn(), post: vi.fn(), delete: vi.fn() },
}));

afterEach(() => vi.clearAllMocks());

describe('redditSearchApi.scan', () => {
  it('posts the scan payload', async () => {
    api.post.mockResolvedValue({ data: { id: 'search-1' } });

    const result = await redditSearchApi.scan({ username: 'someuser' });

    expect(api.post).toHaveBeenCalledWith('/api/reddit-search/scan', { username: 'someuser' });
    expect(result).toEqual({ id: 'search-1' });
  });
});

describe('redditSearchApi.listHistory', () => {
  it('requests paginated history with default skip/limit', async () => {
    api.get.mockResolvedValue({ data: { items: [] } });

    const result = await redditSearchApi.listHistory();

    expect(api.get).toHaveBeenCalledWith('/api/reddit-search/history', { params: { skip: 0, limit: 100 } });
    expect(result).toEqual({ items: [] });
  });
});

describe('redditSearchApi.getHistory', () => {
  it('requests a single history entry by id', async () => {
    api.get.mockResolvedValue({ data: { id: 'search-1' } });

    const result = await redditSearchApi.getHistory('search-1');

    expect(api.get).toHaveBeenCalledWith('/api/reddit-search/history/search-1');
    expect(result).toEqual({ id: 'search-1' });
  });
});

describe('redditSearchApi.deleteHistory', () => {
  it('deletes a history entry by id', async () => {
    api.delete.mockResolvedValue({});

    await redditSearchApi.deleteHistory('search-1');

    expect(api.delete).toHaveBeenCalledWith('/api/reddit-search/history/search-1');
  });
});
