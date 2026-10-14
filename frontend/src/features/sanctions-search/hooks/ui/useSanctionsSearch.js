import { useState, useCallback, useEffect } from 'react';
import { useAtom } from 'jotai';
import { sanctionsSearchApi } from '../../services/api/sanctionsSearchApi';
import { sanctionsSearchStateAtom } from '../../state/sanctionsSearchAtoms';
import { useUrlDrivenLookup } from '../../../../core/hooks/useUrlQuery';
import { createLogger } from '../../../../core/utils/logger';

const logger = createLogger('SanctionsSearch');
const MIN_QUERY_LENGTH = 3;
const isRunnable = (value) => value.length >= MIN_QUERY_LENGTH;

export function useSanctionsSearch() {
  const [{ result, loading, error, lastQuery }, setSearchState] = useAtom(sanctionsSearchStateAtom);
  const [schema, setSchema] = useState('');
  const [schemas, setSchemas] = useState([]);

  useEffect(() => {
    let ignore = false;
    sanctionsSearchApi.getSchemas()
      .then((data) => {
        if (!ignore) setSchemas(data);
      })
      .catch((err) => {
        logger.error('Failed to load sanctions schemas:', err);
      });
    return () => { ignore = true; };
  }, []);

  const search = useCallback(async (queryValue) => {
    setSearchState({ lastQuery: queryValue, result: null, loading: true, error: null });
    try {
      const data = await sanctionsSearchApi.search({
        query: queryValue,
        schema: schema || undefined,
        limit: 50,
      });
      setSearchState({ lastQuery: queryValue, result: data, loading: false, error: null });
    } catch (err) {
      setSearchState({
        lastQuery: queryValue,
        result: null,
        loading: false,
        error: err.response?.data?.detail || err.message || 'Sanctions search failed',
      });
    }
  }, [schema, setSearchState]);

  // The query lives in the URL (?q=): pivots, reloads, bookmarks and Back/Forward all run through it.
  const { urlValue, submit } = useUrlDrivenLookup({ run: search, shownValue: lastQuery, isRunnable });
  const [query, setQuery] = useState(urlValue || lastQuery);
  useEffect(() => { if (urlValue) setQuery(urlValue); }, [urlValue]);

  const runSearch = useCallback((queryOverride) => submit(queryOverride ?? query), [submit, query]);

  return {
    query,
    setQuery,
    schema,
    setSchema,
    schemas,
    result,
    loading,
    error,
    runSearch,
    minQueryLength: MIN_QUERY_LENGTH,
  };
}
