import { useCallback, useState } from 'react';
import { gitReconApi } from '../services/api/gitReconApi';
import { createLogger } from '../../../core/utils/logger';

const logger = createLogger('GitRecon');

export function useGitRecon() {
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const scan = useCallback(async (payload) => {
    setLoading(true);
    setError(null);
    setResult(null);
    try {
      const data = await gitReconApi.scan(payload);
      setResult(data);
      return data;
    } catch (err) {
      logger.error('Scan failed:', err);
      setError(err.response?.data?.detail || err.message);
      return null;
    } finally {
      setLoading(false);
    }
  }, []);

  return { result, loading, error, scan };
}
