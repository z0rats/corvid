import { useState, useEffect, useCallback } from 'react';

export function useRemoteConfig(getFn, updateFn, defaultConfig) {
  const [config, setConfig] = useState(defaultConfig);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    let ignore = false;

    const load = async () => {
      try {
        setLoading(true);
        const data = await getFn();
        if (!ignore) setConfig(data);
      } catch (err) {
        if (!ignore) setError(err);
      } finally {
        if (!ignore) setLoading(false);
      }
    };

    load();
    return () => { ignore = true; };
  }, [getFn]);

  const updateConfig = useCallback(async (updates) => {
    if (saving) return { success: false };

    try {
      setSaving(true);
      setError(null);
      const newConfig = await updateFn({ ...config, ...updates });
      setConfig(newConfig);
      return { success: true };
    } catch (err) {
      setError(err);
      return { success: false, error: err };
    } finally {
      setSaving(false);
    }
  }, [config, saving, updateFn]);

  const setConfigDirect = useCallback((newConfig) => setConfig(newConfig), []);

  return { config, loading, saving, error, updateConfig, setConfig: setConfigDirect };
}
