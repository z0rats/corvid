import { useState, useEffect, useCallback, useRef } from 'react';
import { newsfeedApi } from '../../services/api/newsfeedApi';
import { PAGINATION, DEFAULT_FILTERS } from '../../constants/newsfeedConstants';
import { createLogger } from '../../../../core/utils/logger';

const logger = createLogger('NewsfeedApi');

export function useNewsfeedData() {
  const [result, setResult] = useState([]);
  const [loading, setLoading] = useState(true);
  const [page, setPage] = useState(PAGINATION.DEFAULT_PAGE);
  const [filters, setFilters] = useState(DEFAULT_FILTERS);
  const [refreshCounter, setRefreshCounter] = useState(0);

  useEffect(() => {
    let ignore = false;

    const fetchData = async () => {
      try {
        setLoading(true);
        const data = await newsfeedApi.getArticles({
          ...filters,
          page,
          page_size: PAGINATION.DEFAULT_PAGE_SIZE
        });
        if (!ignore) {
          setResult(data);
          setLoading(false);
        }
      } catch (error) {
        if (!ignore) {
          logger.error('Error fetching newsfeed data:', error);
          setLoading(false);
        }
      }
    };

    fetchData();
    return () => { ignore = true; };
  }, [page, filters, refreshCounter]);

  const updateArticle = useCallback((updatedArticle) => {
    setResult((prev) => ({
      ...prev,
      articles: prev.articles.map((article) =>
        article.id === updatedArticle.id ? updatedArticle : article
      ),
    }));
  }, []);

  const updateArticleField = useCallback((articleId, field, value) => {
    const updateFieldLocally = (items) =>
      items.map((item) =>
        item.id === articleId ? { ...item, [field]: value } : item
      );
    setResult((prev) => ({
      ...prev,
      articles: updateFieldLocally(prev.articles),
    }));
  }, []);

  const applyFilters = useCallback((newFilters) => {
    setFilters(newFilters);
    setPage(PAGINATION.DEFAULT_PAGE);
  }, []);

  const resetFilters = useCallback(() => {
    setFilters(DEFAULT_FILTERS);
    setPage(PAGINATION.DEFAULT_PAGE);
  }, []);

  const refreshData = useCallback(() => {
    setRefreshCounter(prev => prev + 1);
  }, []);

  return {
    result,
    loading,
    page,
    setPage,
    filters,
    setFilters,
    updateArticle,
    updateArticleField,
    applyFilters,
    resetFilters,
    refreshData,
  };
}

export function useArticlesByIds() {
  const [articleDetails, setArticleDetails] = useState({});
  const [articleLoading, setArticleLoading] = useState({});
  const articleDetailsRef = useRef(articleDetails);
  articleDetailsRef.current = articleDetails;

  const fetchArticleDetails = useCallback(async (articleIds) => {
    const idsToFetch = articleIds.filter(id => !articleDetailsRef.current[id]);
    if (idsToFetch.length === 0) return;

    try {
      setArticleLoading(prev => {
        const newLoadingState = { ...prev };
        idsToFetch.forEach(id => newLoadingState[id] = true);
        return newLoadingState;
      });

      const results = await newsfeedApi.getArticlesByIds(idsToFetch);
      const newDetails = Object.fromEntries(results.map(article => [article.id, article]));

      setArticleDetails(prev => ({ ...prev, ...newDetails }));
    } catch (error) {
      logger.error('Error fetching articles:', error);
      const errorDetails = Object.fromEntries(
        idsToFetch.map(id => [id, { error: error.message }])
      );
      setArticleDetails(prev => ({ ...prev, ...errorDetails }));
    } finally {
      setArticleLoading(prev => {
        const newLoadingState = { ...prev };
        idsToFetch.forEach(id => newLoadingState[id] = false);
        return newLoadingState;
      });
    }
  }, []);

  const clearArticleDetails = useCallback(() => {
    setArticleDetails({});
    setArticleLoading({});
  }, []);

  return {
    articleDetails,
    articleLoading,
    fetchArticleDetails,
    clearArticleDetails,
  };
}
