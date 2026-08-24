import { useState, useEffect } from 'react';
import { waybackApi } from '../../services/api/waybackApi';

function isSearchPattern(domain) {
  return domain.includes('*') || domain.includes('?');
}

export function useWaybackLookup(domain, path) {
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

    const fetchWayback = async () => {
      try {
        setLoading(true);
        setError(null);
        const result = await waybackApi.lookupWayback(domain, path);
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

    fetchWayback();
    return () => { ignore = true; };
  }, [domain, path]);

  return { data, loading, error, unsupported };
}
