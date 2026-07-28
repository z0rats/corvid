import { useEffect, useState, useCallback, useRef } from 'react';
import { createLogger } from '../utils/logger';

const logger = createLogger('HistoryDetail');

/**
 * Shared load/loading/not-found boilerplate for a "history" detail record.
 * `fetchOne` is only ever called with `id` on mount/id-change - each feature
 * still owns how it renders the record.
 */
export function useHistoryDetail(fetchOne, id) {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const fetchOneRef = useRef(fetchOne);
  fetchOneRef.current = fetchOne;

  const load = useCallback(async () => {
    try {
      setLoading(true);
      const result = await fetchOneRef.current(id);
      setData(result);
    } catch (err) {
      logger.error('Failed to load history detail:', err);
    } finally {
      setLoading(false);
    }
  }, [id]);

  useEffect(() => { load(); }, [load]);

  return { data, loading };
}
