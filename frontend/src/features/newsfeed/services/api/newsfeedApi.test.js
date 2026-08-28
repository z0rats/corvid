import api from '../../../../core/services/baseApi';
import { newsfeedApi } from './newsfeedApi';

vi.mock('../../../../core/services/baseApi', () => ({
  default: { get: vi.fn(), post: vi.fn(), patch: vi.fn() },
}));

afterEach(() => vi.clearAllMocks());

describe('newsfeedApi.getArticles', () => {
  it('strips null/undefined/empty-string params before requesting', async () => {
    api.get.mockResolvedValue({ data: { items: [] } });

    const result = await newsfeedApi.getArticles({
      source: 'thehackernews',
      severity: null,
      keyword: undefined,
      tag: '',
      skip: 0,
    });

    expect(api.get).toHaveBeenCalledWith('/api/newsfeed/articles', {
      params: { source: 'thehackernews', skip: 0 },
    });
    expect(result).toEqual({ items: [] });
  });
});

describe('newsfeedApi.getArticlesByIds', () => {
  it('posts the requested article ids', async () => {
    api.post.mockResolvedValue({ data: [{ id: 1 }] });

    const result = await newsfeedApi.getArticlesByIds([1, 2, 3]);

    expect(api.post).toHaveBeenCalledWith('/api/newsfeed/articles/bulk', { article_ids: [1, 2, 3] });
    expect(result).toEqual([{ id: 1 }]);
  });
});

describe('newsfeedApi.updateArticle', () => {
  it('patches the given article fields', async () => {
    api.patch.mockResolvedValue({ data: { id: 1, read: true } });

    const result = await newsfeedApi.updateArticle(1, { read: true });

    expect(api.patch).toHaveBeenCalledWith('/api/newsfeed/article/1', { read: true });
    expect(result).toEqual({ id: 1, read: true });
  });
});

describe('newsfeedApi.analyzeArticle', () => {
  it('posts with default force/mode when omitted', async () => {
    api.post.mockResolvedValue({ data: { analysis: {} } });

    const result = await newsfeedApi.analyzeArticle(1);

    expect(api.post).toHaveBeenCalledWith('/api/newsfeed/analyze/1', { force: false, mode: 'all' });
    expect(result).toEqual({ analysis: {} });
  });

  it('passes through explicit force/mode', async () => {
    api.post.mockResolvedValue({ data: { analysis: {} } });

    await newsfeedApi.analyzeArticle(1, true, 'iocs');

    expect(api.post).toHaveBeenCalledWith('/api/newsfeed/analyze/1', { force: true, mode: 'iocs' });
  });
});

describe('newsfeedApi.fetchAndGetNews', () => {
  it('posts to trigger an immediate fetch', async () => {
    api.post.mockResolvedValue({ data: { fetched: 5 } });

    const result = await newsfeedApi.fetchAndGetNews();

    expect(api.post).toHaveBeenCalledWith('/api/newsfeed/fetch_and_get');
    expect(result).toEqual({ fetched: 5 });
  });
});

describe('newsfeedApi.getRecentArticles', () => {
  it('requests recent articles for the given time filter', async () => {
    api.get.mockResolvedValue({ data: { items: [] } });

    const result = await newsfeedApi.getRecentArticles('24h');

    expect(api.get).toHaveBeenCalledWith('/api/newsfeed/articles/recent?time_filter=24h');
    expect(result).toEqual({ items: [] });
  });
});
