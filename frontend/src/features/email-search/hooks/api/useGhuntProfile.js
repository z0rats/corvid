import { useEffect, useState } from 'react';
import { ghuntProfileApi } from '../../services/api/ghuntProfileApi';
import { createLogger } from '../../../../core/utils/logger';

const logger = createLogger('GhuntProfile');

export function useGhuntProfile() {
  const [health, setHealth] = useState(null);
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    let ignore = false;
    ghuntProfileApi
      .getHealth()
      .then((data) => {
        if (!ignore) setHealth(data);
      })
      .catch((err) => {
        logger.error('Error fetching GHunt health:', err);
      });
    return () => { ignore = true; };
  }, []);

  const lookup = async (email) => {
    setLoading(true);
    setError(null);
    try {
      const profile = await ghuntProfileApi.lookup(email);
      setResult(profile);
    } catch (err) {
      logger.error('Error running GHunt profile lookup:', err);
      const errorCode = err.response?.data?.error_code;
      setError({ code: errorCode, message: err.response?.data?.detail || err.message });
    }
    setLoading(false);
  };

  const reset = () => {
    setResult(null);
    setError(null);
  };

  return { health, result, loading, error, lookup, reset };
}
