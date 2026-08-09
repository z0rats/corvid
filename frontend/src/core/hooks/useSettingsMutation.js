import { useCallback, useState } from 'react';

/**
 * The `setLoading(true); setError(null); try {...} catch {...} finally {...}` shape shared by
 * every settings feature's API hook (useApiKeys, useGeneralSettings, useCommandPaletteSettings,
 * ...). `run` owns exactly that scaffolding plus the `err.response?.data?.detail || errorFallback`
 * resolution; it knows nothing about i18n or atom updates - `asyncFn` does the actual API call and
 * returns whatever success payload the caller wants merged into `{ success: true, ... }`
 * (`{ message }` for a mutation, `{ data }` for a getter). One `loading`/`error` pair per hook
 * instance, shared across every operation it exposes - matches the pre-existing behavior of the
 * hooks this replaces.
 */
export function useSettingsMutation() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const run = useCallback(async (asyncFn, errorFallback) => {
    setLoading(true);
    setError(null);
    try {
      const result = await asyncFn();
      return { success: true, ...result };
    } catch (err) {
      const message = err.response?.data?.detail || errorFallback;
      setError(message);
      return { success: false, message };
    } finally {
      setLoading(false);
    }
  }, []);

  return { loading, error, run };
}
