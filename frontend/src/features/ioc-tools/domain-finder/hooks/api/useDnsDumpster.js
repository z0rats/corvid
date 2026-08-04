import { useState, useEffect } from 'react';
import { dnsDumpsterApi } from '../../services/api/dnsDumpsterApi';

function isSearchPattern(domain) {
  return domain.includes('*') || domain.includes('?');
}

export function useDnsDumpster(domain) {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [notConfigured, setNotConfigured] = useState(false);
  const unsupported = Boolean(domain) && isSearchPattern(domain);

  useEffect(() => {
    if (!domain || isSearchPattern(domain)) {
      setData(null);
      setLoading(false);
      setError(null);
      setNotConfigured(false);
      return;
    }

    let ignore = false;

    const fetchDnsDumpster = async () => {
      try {
        setLoading(true);
        setError(null);
        setNotConfigured(false);
        const result = await dnsDumpsterApi.lookupDnsDumpster(domain);
        if (!ignore) {
          setData(result);
        }
      } catch (err) {
        if (!ignore) {
          if (err.response?.data?.error_code === 'DNSDUMPSTER_NOT_CONFIGURED') {
            setNotConfigured(true);
          } else {
            setError(err.response?.data?.detail || err.response?.data?.message || err.message);
          }
          setData(null);
        }
      } finally {
        if (!ignore) {
          setLoading(false);
        }
      }
    };

    fetchDnsDumpster();
    return () => { ignore = true; };
  }, [domain]);

  return { data, loading, error, notConfigured, unsupported };
}
