import { useState, useEffect } from 'react';
import { hackertargetApi } from '../../services/api/hackertargetApi';

function isSearchPattern(domain) {
  return domain.includes('*') || domain.includes('?');
}

export function useHackertargetSubdomains(domain) {
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

    const fetchHackertargetSubdomains = async () => {
      try {
        setLoading(true);
        setError(null);
        const result = await hackertargetApi.lookupHackertargetSubdomains(domain);
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

    fetchHackertargetSubdomains();
    return () => { ignore = true; };
  }, [domain]);

  return { data, loading, error, unsupported };
}
