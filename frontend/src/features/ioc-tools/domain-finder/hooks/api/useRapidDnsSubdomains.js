import { useState, useEffect } from 'react';
import { rapidDnsApi } from '../../services/api/rapidDnsApi';

function isSearchPattern(domain) {
  return domain.includes('*') || domain.includes('?');
}

export function useRapidDnsSubdomains(domain) {
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

    const fetchRapidDnsSubdomains = async () => {
      try {
        setLoading(true);
        setError(null);
        const result = await rapidDnsApi.lookupRapidDnsSubdomains(domain);
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

    fetchRapidDnsSubdomains();
    return () => { ignore = true; };
  }, [domain]);

  return { data, loading, error, unsupported };
}
