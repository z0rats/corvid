import { useCallback, useEffect, useState } from 'react';
import { youtubeApi } from '../../services/api/youtubeApi';

const INITIAL_RESULTS = { comments: [], nextPageToken: null, truncated: false, hasSearched: false };

export function useYoutubeComments(url) {
  const [query, setQuery] = useState('');
  const [order, setOrder] = useState('relevance');
  const [results, setResults] = useState(INITIAL_RESULTS);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  // A new video invalidates whatever was fetched for the previous one.
  useEffect(() => {
    setResults(INITIAL_RESULTS);
    setError(null);
  }, [url]);

  const runQuery = useCallback(async (pageToken) => {
    if (!url) return;
    setLoading(true);
    setError(null);
    try {
      const data = await youtubeApi.comments({ url, query: query.trim(), order, pageToken });
      setResults((prev) => ({
        comments: pageToken ? [...prev.comments, ...data.comments] : data.comments,
        nextPageToken: data.next_page_token,
        truncated: data.truncated,
        hasSearched: true,
      }));
    } catch (err) {
      setError(err.response?.data?.detail || err.message || 'Failed to load comments');
    } finally {
      setLoading(false);
    }
  }, [url, query, order]);

  return {
    query,
    setQuery,
    order,
    setOrder,
    loading,
    error,
    hasSearched: results.hasSearched,
    comments: results.comments,
    nextPageToken: results.nextPageToken,
    truncated: results.truncated,
    search: () => runQuery(undefined),
    loadMore: () => runQuery(results.nextPageToken),
  };
}
