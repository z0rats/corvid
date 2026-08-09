import { act, renderHook, waitFor } from '@testing-library/react';
import { useRedditSearch } from './useRedditSearch';
import { redditSearchApi } from '../services/api/redditSearchApi';

vi.mock('../services/api/redditSearchApi');

function page(items, hasMore, searchId = 'search-1') {
  return {
    items,
    sources: [],
    has_more: hasMore,
    search_id: searchId,
  };
}

function post(id, createdUtc) {
  return { id, created_utc: createdUtc };
}

describe('useRedditSearch', () => {
  afterEach(() => vi.clearAllMocks());

  it('fetches posts then comments on search and seeds the cursor stack from the first page', async () => {
    redditSearchApi.scan
      .mockResolvedValueOnce(page([post('p1', 300), post('p2', 200)], true))
      .mockResolvedValueOnce(page([post('c1', 300)], false));

    const { result } = renderHook(() => useRedditSearch());

    await act(async () => {
      await result.current.search('alice');
    });

    expect(redditSearchApi.scan).toHaveBeenNthCalledWith(1, expect.objectContaining({
      username: 'alice', kind: 'posts', cursor: null, search_id: null,
    }));
    expect(redditSearchApi.scan).toHaveBeenNthCalledWith(2, expect.objectContaining({
      username: 'alice', kind: 'comments', cursor: null, search_id: 'search-1',
    }));
    expect(result.current.posts.items.map((i) => i.id)).toEqual(['p1', 'p2']);
    expect(result.current.posts.hasMore).toBe(true);
    expect(result.current.searchId).toBe('search-1');
  });

  it('goNext requests the next page using the last item\'s created_utc as the "before" cursor', async () => {
    redditSearchApi.scan
      .mockResolvedValueOnce(page([post('p1', 300), post('p2', 200)], true))
      .mockResolvedValueOnce(page([], false)); // empty comments page

    const { result } = renderHook(() => useRedditSearch());
    await act(async () => { await result.current.search('alice'); });

    redditSearchApi.scan.mockResolvedValueOnce(page([post('p3', 100)], false));
    await act(async () => { await result.current.goNext('posts'); });

    expect(redditSearchApi.scan).toHaveBeenLastCalledWith(expect.objectContaining({
      cursor: { before: 200 },
    }));
    expect(result.current.posts.items.map((i) => i.id)).toEqual(['p3']);
    expect(result.current.posts.page).toBe(2);
    expect(result.current.posts.hasMore).toBe(false);
  });

  it('goPrev from page 2 back to page 1 refetches with a null cursor (verified correct, not an off-by-one)', async () => {
    redditSearchApi.scan
      .mockResolvedValueOnce(page([post('p1', 300), post('p2', 200)], true))
      .mockResolvedValueOnce(page([], false));

    const { result } = renderHook(() => useRedditSearch());
    await act(async () => { await result.current.search('alice'); });

    redditSearchApi.scan.mockResolvedValueOnce(page([post('p3', 100)], false));
    await act(async () => { await result.current.goNext('posts'); });

    redditSearchApi.scan.mockResolvedValueOnce(page([post('p1', 300), post('p2', 200)], true));
    await act(async () => { await result.current.goPrev('posts'); });

    // Popping the only remaining stack frame leaves no earlier boundary to cursor from - a plain
    // `stack[stack.length - 2]` read on a length-1 array returns undefined (not a throw), which
    // correctly resolves to a null cursor ("start from page 1") rather than an off-by-one.
    expect(redditSearchApi.scan).toHaveBeenLastCalledWith(expect.objectContaining({ cursor: null }));
    expect(result.current.posts.items.map((i) => i.id)).toEqual(['p1', 'p2']);
    expect(result.current.posts.page).toBe(1);
  });

  it('goPrev is a no-op already on page 1', async () => {
    redditSearchApi.scan
      .mockResolvedValueOnce(page([post('p1', 300)], false))
      .mockResolvedValueOnce(page([], false));

    const { result } = renderHook(() => useRedditSearch());
    await act(async () => { await result.current.search('alice'); });

    const callsBefore = redditSearchApi.scan.mock.calls.length;
    await act(async () => { await result.current.goPrev('posts'); });

    expect(redditSearchApi.scan).toHaveBeenCalledTimes(callsBefore);
  });

  it('sets a tab error and stops loading when the API call fails, without touching the other tab', async () => {
    redditSearchApi.scan
      .mockResolvedValueOnce(page([post('p1', 300)], false))
      .mockRejectedValueOnce({ response: { data: { detail: 'boom' } } });

    const { result } = renderHook(() => useRedditSearch());
    await act(async () => { await result.current.search('alice'); });

    await waitFor(() => expect(result.current.comments.error).toBe('boom'));
    expect(result.current.comments.loading).toBe(false);
    expect(result.current.posts.error).toBeNull();
  });
});
