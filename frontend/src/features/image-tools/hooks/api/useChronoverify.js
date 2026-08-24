import { useState } from 'react';
import { chronoverifyApi } from '../../services/api/chronoverifyApi';
import { createLogger } from '../../../../core/utils/logger';

const logger = createLogger('Chronoverify');

export function useChronoverify() {
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const checkProvenance = async (file) => {
    setLoading(true);
    setError(null);
    try {
      const provenanceResult = await chronoverifyApi.checkProvenance(file);
      setResult(provenanceResult);
    } catch (err) {
      logger.error('Error running ChronoVerify provenance check:', err);
      setError(err.response?.data?.detail || err.message || 'Failed to run provenance check');
    }
    setLoading(false);
  };

  const reset = () => {
    setResult(null);
    setError(null);
  };

  return { result, loading, error, checkProvenance, reset };
}
