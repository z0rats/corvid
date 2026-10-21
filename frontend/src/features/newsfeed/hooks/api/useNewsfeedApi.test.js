import { renderHook, act, waitFor } from '@testing-library/react';
import { newsfeedApi } from '../../services/api/newsfeedApi';
import { useNewsfeedData, useArticlesByIds } from './useNewsfeedApi';
import { DEFAULT_FILTERS, PAGINATION } from '../../constants/newsfeedConstants';

vi.mock('../../services/api/newsfeedApi', () => ({
  newsfeedApi: { getArticles: vi.fn(), getArticlesByIds: vi.fn() },
}));

const page = (ids) => ({ articles: ids.map((id) => ({ id, title: `t${id}`, tlp: 'TLP:CLEAR' })), total: ids.length });

function deferred() {
  let resolve;
  const promise = new Promise((r) => { resolve = r; });
  return { promise, resolve };
}

afterEach(() => vi.clearAllMocks());

describe('useNewsfeedData', () => {
  it('fetches the first page with the default filters', async () => {
    newsfeedApi.getArticles.mockResolvedValue(page([1, 2]));
    const { result } = renderHook(() => useNewsfeedData());
    expect(result.current.loading).toBe(true);
    await waitFor(() => expect(result.current.loading).toBe(false));
    expect(result.current.result.articles).toHaveLength(2);
    expect(newsfeedApi.getArticles).toHaveBeenCalledWith({
      ...DEFAULT_FILTERS, page: PAGINATION.DEFAULT_PAGE, page_size: PAGINATION.DEFAULT_PAGE_SIZE,
    });
  });

  it('ignores a slow response for a page the user already left', async () => {
    const slow = deferred();
    newsfeedApi.getArticles
      .mockReturnValueOnce(slow.promise)
      .mockResolvedValueOnce(page([20, 21]));
    const { result } = renderHook(() => useNewsfeedData());

    act(() => result.current.setPage(2));
    await waitFor(() => expect(result.current.result.articles?.[0]?.id).toBe(20));

    await act(async () => slow.resolve(page([1])));
    expect(result.current.result.articles.map((a) => a.id)).toEqual([20, 21]);
  });

  it('applying or resetting filters returns to the first page', async () => {
    newsfeedApi.getArticles.mockResolvedValue(page([1]));
    const { result } = renderHook(() => useNewsfeedData());
    await waitFor(() => expect(result.current.loading).toBe(false));

    act(() => result.current.setPage(3));
    act(() => result.current.applyFilters({ ...DEFAULT_FILTERS, has_iocs: true }));
    expect(result.current.page).toBe(PAGINATION.DEFAULT_PAGE);
    await waitFor(() => expect(newsfeedApi.getArticles).toHaveBeenLastCalledWith(
      expect.objectContaining({ has_iocs: true, page: PAGINATION.DEFAULT_PAGE }),
    ));

    act(() => result.current.setPage(2));
    act(() => result.current.resetFilters());
    expect(result.current.filters).toEqual(DEFAULT_FILTERS);
    expect(result.current.page).toBe(PAGINATION.DEFAULT_PAGE);
  });

  it('refreshData refetches with the same parameters', async () => {
    newsfeedApi.getArticles.mockResolvedValue(page([1]));
    const { result } = renderHook(() => useNewsfeedData());
    await waitFor(() => expect(newsfeedApi.getArticles).toHaveBeenCalledTimes(1));
    act(() => result.current.refreshData());
    await waitFor(() => expect(newsfeedApi.getArticles).toHaveBeenCalledTimes(2));
  });

  it('a failed fetch stops loading and keeps the previous result', async () => {
    newsfeedApi.getArticles.mockResolvedValueOnce(page([1])).mockRejectedValueOnce(new Error('500'));
    const { result } = renderHook(() => useNewsfeedData());
    await waitFor(() => expect(result.current.loading).toBe(false));
    act(() => result.current.refreshData());
    await waitFor(() => expect(newsfeedApi.getArticles).toHaveBeenCalledTimes(2));
    await waitFor(() => expect(result.current.loading).toBe(false));
    expect(result.current.result.articles.map((a) => a.id)).toEqual([1]);
  });

  it('updates a single article or field in place', async () => {
    newsfeedApi.getArticles.mockResolvedValue(page([1, 2]));
    const { result } = renderHook(() => useNewsfeedData());
    await waitFor(() => expect(result.current.loading).toBe(false));

    act(() => result.current.updateArticle({ id: 2, title: 'new', tlp: 'TLP:RED' }));
    act(() => result.current.updateArticleField(1, 'tlp', 'TLP:AMBER'));

    const [a1, a2] = result.current.result.articles;
    expect(a1).toEqual({ id: 1, title: 't1', tlp: 'TLP:AMBER' });
    expect(a2).toEqual({ id: 2, title: 'new', tlp: 'TLP:RED' });
  });
});

describe('useArticlesByIds', () => {
  it('fetches only ids it does not have yet', async () => {
    newsfeedApi.getArticlesByIds.mockImplementation(async (ids) => ids.map((id) => ({ id })));
    const { result } = renderHook(() => useArticlesByIds());

    await act(async () => result.current.fetchArticleDetails([1, 2]));
    await act(async () => result.current.fetchArticleDetails([2, 3]));
    await act(async () => result.current.fetchArticleDetails([1, 3]));

    expect(newsfeedApi.getArticlesByIds.mock.calls).toEqual([[[1, 2]], [[3]]]);
    expect(Object.keys(result.current.articleDetails)).toEqual(['1', '2', '3']);
    expect(result.current.articleLoading).toEqual({ 1: false, 2: false, 3: false });
  });

  it('records a per-id error on failure and can be cleared', async () => {
    newsfeedApi.getArticlesByIds.mockRejectedValue(new Error('timeout'));
    const { result } = renderHook(() => useArticlesByIds());
    await act(async () => result.current.fetchArticleDetails([7]));
    expect(result.current.articleDetails).toEqual({ 7: { error: 'timeout' } });

    act(() => result.current.clearArticleDetails());
    expect(result.current.articleDetails).toEqual({});
    expect(result.current.articleLoading).toEqual({});
  });
});
