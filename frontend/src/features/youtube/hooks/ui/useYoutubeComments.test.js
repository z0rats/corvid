import { act, renderHook, waitFor } from '@testing-library/react';
import { useYoutubeComments } from './useYoutubeComments';
import { youtubeApi } from '../../services/api/youtubeApi';

vi.mock('../../services/api/youtubeApi');

const VIDEO_URL = 'https://www.youtube.com/watch?v=dQw4w9WgXcQ';

describe('useYoutubeComments', () => {
  afterEach(() => {
    vi.clearAllMocks();
  });

  it('starts with no comments and hasSearched false', () => {
    const { result } = renderHook(() => useYoutubeComments(VIDEO_URL));

    expect(result.current.comments).toEqual([]);
    expect(result.current.hasSearched).toBe(false);
    expect(result.current.loading).toBe(false);
    expect(result.current.error).toBeNull();
  });

  it('search() replaces comments and stores pagination/truncation state', async () => {
    youtubeApi.comments.mockResolvedValue({
      comments: [{ comment_id: 'c1', text: 'hi' }],
      next_page_token: 'p2',
      truncated: true,
    });

    const { result } = renderHook(() => useYoutubeComments(VIDEO_URL));

    await act(async () => {
      await result.current.search();
    });

    await waitFor(() => expect(result.current.loading).toBe(false));
    expect(result.current.hasSearched).toBe(true);
    expect(result.current.comments).toEqual([{ comment_id: 'c1', text: 'hi' }]);
    expect(result.current.nextPageToken).toBe('p2');
    expect(result.current.truncated).toBe(true);
    expect(youtubeApi.comments).toHaveBeenCalledWith({ url: VIDEO_URL, query: '', order: 'relevance', pageToken: undefined });
  });

  it('loadMore() appends to the existing comments using the stored page token', async () => {
    youtubeApi.comments
      .mockResolvedValueOnce({ comments: [{ comment_id: 'c1', text: 'first' }], next_page_token: 'p2', truncated: false })
      .mockResolvedValueOnce({ comments: [{ comment_id: 'c2', text: 'second' }], next_page_token: null, truncated: false });

    const { result } = renderHook(() => useYoutubeComments(VIDEO_URL));

    await act(async () => {
      await result.current.search();
    });
    await act(async () => {
      await result.current.loadMore();
    });

    expect(result.current.comments.map((c) => c.comment_id)).toEqual(['c1', 'c2']);
    expect(result.current.nextPageToken).toBeNull();
    expect(youtubeApi.comments).toHaveBeenNthCalledWith(2, { url: VIDEO_URL, query: '', order: 'relevance', pageToken: 'p2' });
  });

  it('surfaces the API error message on failure', async () => {
    youtubeApi.comments.mockRejectedValue({
      response: { data: { detail: 'A YouTube Data API key is required for comments.' } },
    });

    const { result } = renderHook(() => useYoutubeComments(VIDEO_URL));

    await act(async () => {
      await result.current.search();
    });

    expect(result.current.error).toBe('A YouTube Data API key is required for comments.');
    expect(result.current.comments).toEqual([]);
  });

  it('resets comments/pagination when the video URL changes', async () => {
    youtubeApi.comments.mockResolvedValue({ comments: [{ comment_id: 'c1' }], next_page_token: 'p2', truncated: false });

    const { result, rerender } = renderHook(({ url }) => useYoutubeComments(url), { initialProps: { url: VIDEO_URL } });

    await act(async () => {
      await result.current.search();
    });
    expect(result.current.comments).toHaveLength(1);

    rerender({ url: 'https://www.youtube.com/watch?v=anotherVideo1' });

    expect(result.current.comments).toEqual([]);
    expect(result.current.hasSearched).toBe(false);
    expect(result.current.nextPageToken).toBeNull();
  });

  it('does not call the API when url is empty', async () => {
    const { result } = renderHook(() => useYoutubeComments(''));

    await act(async () => {
      await result.current.search();
    });

    expect(youtubeApi.comments).not.toHaveBeenCalled();
  });
});
