import { useState, useEffect } from 'react';
import { temporalAnalysisApi } from '../../services/api/temporalAnalysisApi';

function isSearchPattern(domain) {
  return domain.includes('*') || domain.includes('?');
}

export function useTemporalAnalysis(domain) {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const unsupported = Boolean(domain) && isSearchPattern(domain);

  useEffect(() => {
    if (!domain || isSearchPattern(domain)) {
      setData(null);
      setLoading(false);
      setError(null);
      return;
    }

    let ignore = false;

    const fetchTemporalAnalysis = async () => {
      try {
        setLoading(true);
        setError(null);
        const result = await temporalAnalysisApi.lookupTemporalAnalysis(domain);
        if (!ignore) {
          setData(result);
        }
      } catch (err) {
        if (!ignore) {
          setError(err.response?.data?.detail || err.response?.data?.message || err.message);
          setData(null);
        }
      } finally {
        if (!ignore) {
          setLoading(false);
        }
      }
    };

    fetchTemporalAnalysis();
    return () => { ignore = true; };
  }, [domain]);

  return { data, loading, error, unsupported };
}
