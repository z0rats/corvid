import { useState, useEffect } from 'react';
import { domainMonitoringApi } from '../../services/api/domainMonitoringApi';

export function useDomainSearch(domain) {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (!domain) {
      setData(null);
      setLoading(false);
      setError(null);
      return;
    }

    let ignore = false;

    const searchDomains = async () => {
      try {
        setLoading(true);
        setError(null);
        const result = await domainMonitoringApi.searchDomains(domain);
        if (!ignore) {
          setData(result);
        }
      } catch (err) {
        if (!ignore) {
          setError(err.message || 'Failed to search domains');
          setData(null);
        }
      } finally {
        if (!ignore) {
          setLoading(false);
        }
      }
    };

    searchDomains();
    return () => { ignore = true; };
  }, [domain]);

  const refetch = () => {
    if (domain) {
      const searchDomains = async () => {
        try {
          setLoading(true);
          setError(null);
          const result = await domainMonitoringApi.searchDomains(domain);
          setData(result);
        } catch (err) {
          setError(err.message || 'Failed to search domains');
          setData(null);
        } finally {
          setLoading(false);
        }
      };
      searchDomains();
    }
  };

  return {
    data,
    loading,
    error,
    refetch
  };
}
