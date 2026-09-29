import { useState, useCallback, useEffect } from 'react';
import { useAtom } from 'jotai';
import { sanctionsSearchApi } from '../../services/api/sanctionsSearchApi';
import { sanctionsSearchStateAtom } from '../../state/sanctionsSearchAtoms';
import { usePrefillFromQuery } from '../../../../core/hooks/usePrefillFromQuery';
import { createLogger } from '../../../../core/utils/logger';

const logger = createLogger('SanctionsSearch');
const MIN_QUERY_LENGTH = 3;

export function useSanctionsSearch() {
  const [query, setQuery] = useState('');
  const [schema, setSchema] = useState('');
  const [schemas, setSchemas] = useState([]);
  const [{ result, loading, error }, setSearchState] = useAtom(sanctionsSearchStateAtom);

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

  const runSearch = useCallback(async (queryOverride) => {
    const queryValue = (queryOverride ?? query).trim();
    if (queryValue.length < MIN_QUERY_LENGTH) return;

    setSearchState({ result: null, loading: true, error: null });
    try {
      const data = await sanctionsSearchApi.search({
        query: queryValue,
        schema: schema || undefined,
        limit: 50,
      });
      setSearchState({ result: data, loading: false, error: null });
    } catch (err) {
      setSearchState({
        result: null,
        loading: false,
        error: err.response?.data?.detail || err.message || 'Sanctions search failed',
      });
    }
  }, [query, schema, setSearchState]);

  usePrefillFromQuery(useCallback((value) => {
    setQuery(value);
    runSearch(value);
  }, [runSearch]));

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
