import { useCallback, useRef, useState } from 'react';
import { redditSearchApi } from '../services/api/redditSearchApi';
import { createLogger } from '../../../core/utils/logger';

const logger = createLogger('RedditSearch');

const emptyTab = () => ({ items: [], sources: [], page: 1, hasMore: false, loading: false, error: null });

function boundary(items) {
  return { first: items[0].created_utc, last: items[items.length - 1].created_utc };
}

export function useRedditSearch() {
  const [username, setUsername] = useState('');
  const [searchId, setSearchId] = useState(null);
  const [posts, setPosts] = useState(emptyTab());
  const [comments, setComments] = useState(emptyTab());

  const filtersRef = useRef({});
  const searchIdRef = useRef(null);
  const cursorStacks = useRef({ posts: [], comments: [] });

  const setterFor = useCallback((kind) => (kind === 'posts' ? setPosts : setComments), []);

  const fetchPage = useCallback(async (kind, uname, cursor, sid) => {
    const setTab = setterFor(kind);
    setTab((prev) => ({ ...prev, loading: true, error: null }));
    try {
      const data = await redditSearchApi.scan({
        username: uname,
        kind,
        filters: filtersRef.current,
        cursor: cursor || null,
        search_id: sid,
      });
      if (!searchIdRef.current) {
        searchIdRef.current = data.search_id;
        setSearchId(data.search_id);
      }
      return data;
    } catch (err) {
      logger.error(`Failed to fetch ${kind}:`, err);
      setTab((prev) => ({ ...prev, loading: false, error: err.response?.data?.detail || err.message }));
      return null;
    }
  }, [setterFor]);

  const search = useCallback(async (rawUsername, filters = {}) => {
    const uname = rawUsername.trim();
    if (!uname) return;

    filtersRef.current = filters;
    searchIdRef.current = null;
    cursorStacks.current = { posts: [], comments: [] };
    setUsername(uname);
    setSearchId(null);
    setPosts(emptyTab());
    setComments(emptyTab());

    const postsData = await fetchPage('posts', uname, null, null);
    if (postsData) {
      if (postsData.items.length > 0) cursorStacks.current.posts = [boundary(postsData.items)];
      setPosts({ items: postsData.items, sources: postsData.sources, page: 1, hasMore: postsData.has_more, loading: false, error: null });
    }

    const commentsData = await fetchPage('comments', uname, null, searchIdRef.current);
    if (commentsData) {
      if (commentsData.items.length > 0) cursorStacks.current.comments = [boundary(commentsData.items)];
      setComments({ items: commentsData.items, sources: commentsData.sources, page: 1, hasMore: commentsData.has_more, loading: false, error: null });
    }
  }, [fetchPage]);

  const goNext = useCallback(async (kind) => {
    const stack = cursorStacks.current[kind];
    const current = stack[stack.length - 1];
    if (!current) return;

    const data = await fetchPage(kind, username, { before: current.last }, searchIdRef.current);
    if (!data) return;

    const setTab = setterFor(kind);
    if (data.items.length > 0) {
      cursorStacks.current[kind] = [...stack, boundary(data.items)];
      setTab((prev) => ({ ...prev, items: data.items, sources: data.sources, page: prev.page + 1, hasMore: data.has_more, loading: false, error: null }));
    } else {
      setTab((prev) => ({ ...prev, loading: false, hasMore: false }));
    }
  }, [fetchPage, username, setterFor]);

  const goPrev = useCallback(async (kind) => {
    const stack = cursorStacks.current[kind];
    if (stack.length <= 1) return;

    const newStack = stack.slice(0, -1);
    const prevEntry = newStack[newStack.length - 2];
    const cursor = prevEntry ? { after: prevEntry.first } : null;

    const data = await fetchPage(kind, username, cursor, searchIdRef.current);
    if (!data) return;

    if (data.items.length > 0) {
      newStack[newStack.length - 1] = boundary(data.items);
    }
    cursorStacks.current[kind] = newStack;

    const setTab = setterFor(kind);
    setTab((prev) => ({ ...prev, items: data.items, sources: data.sources, page: prev.page - 1, hasMore: true, loading: false, error: null }));
  }, [fetchPage, username, setterFor]);

  return { username, searchId, posts, comments, search, goNext, goPrev };
}
