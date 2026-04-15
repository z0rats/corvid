import { useState, useEffect } from 'react';

export function useTrendsFetch(apiFn, args, deps) {
  const [data, setData] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    let ignore = false;

    const fetchData = async () => {
      try {
        setLoading(true);
        setError(null);
        const result = await apiFn(...args);
        if (!ignore) {
          setData(Array.isArray(result) ? result : []);
        }
      } catch (err) {
        if (!ignore) {
          setError(err.message);
          setData([]);
        }
      } finally {
        if (!ignore) {
          setLoading(false);
        }
      }
    };

    fetchData();
    return () => { ignore = true; };
  }, deps); // eslint-disable-line react-hooks/exhaustive-deps

  return { data, loading, error };
}
