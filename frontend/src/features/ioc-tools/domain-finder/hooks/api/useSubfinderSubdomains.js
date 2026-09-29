import { useState } from 'react';
import { subfinderApi } from '../../services/api/subfinderApi';

function isSearchPattern(domain) {
  return domain.includes('*') || domain.includes('?');
}

export function useSubfinderSubdomains(domain) {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const unsupported = Boolean(domain) && isSearchPattern(domain);

  const run = async () => {
    setLoading(true);
    setError(null);
    try {
      const result = await subfinderApi.lookupSubfinderSubdomains(domain);
      setData(result);
    } catch (err) {
      setError(err.response?.data?.detail || err.response?.data?.message || err.message);
      setData(null);
    } finally {
      setLoading(false);
    }
  };

  return { data, loading, error, unsupported, run };
}
