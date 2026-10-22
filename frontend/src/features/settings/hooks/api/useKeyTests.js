import { useState, useCallback, useRef } from 'react';
import { useTranslation } from 'react-i18next';
import { settingsApi } from '../../services/api/settingsApi';

/**
 * Live API key checks for Settings → API Keys. Results are live only (never persisted), keyed
 * by service key; `testing` holds the services with a check in flight.
 *
 * A single test and "Test all" can overlap (e.g. the auto-test after a save during a Test all),
 * so every request takes a token from one counter and a result is applied only if no newer
 * request for that service has been applied since.
 */
export function useKeyTests() {
  const { t } = useTranslation('settings');
  const [results, setResults] = useState({});
  const [testing, setTesting] = useState(() => new Set());
  const [testingAll, setTestingAll] = useState(false);
  const [error, setError] = useState(null);
  const counter = useRef(0);
  const latest = useRef({});

  // A 422's `detail` is a list of objects - never render that as text.
  const errorText = useCallback((err) => {
    const detail = err?.response?.data?.detail;
    return typeof detail === 'string' && detail ? detail : t('keyTest.requestFailed');
  }, [t]);

  const applyIfNewest = (serviceKey, token, result) => {
    if ((latest.current[serviceKey] ?? 0) > token) return;
    latest.current[serviceKey] = token;
    setResults((prev) => ({ ...prev, [serviceKey]: result }));
  };

  const setInFlight = (serviceKey, inFlight) => setTesting((prev) => {
    const next = new Set(prev);
    if (inFlight) next.add(serviceKey); else next.delete(serviceKey);
    return next;
  });

  /**
   * `afterSave`: the automatic check right after a key is saved. For a multi-key service the
   * other keys may not be in yet, so a `not_configured` answer is dropped instead of shown.
   */
  const testService = useCallback(async (serviceKey, { afterSave = false } = {}) => {
    counter.current += 1;
    const token = counter.current;
    latest.current[serviceKey] = token;
    setInFlight(serviceKey, true);
    try {
      const result = await settingsApi.testApiKey(serviceKey);
      if (afterSave && result.status === 'not_configured') return;
      applyIfNewest(serviceKey, token, result);
    } catch (err) {
      applyIfNewest(serviceKey, token, { service: serviceKey, status: 'error', detail: errorText(err) });
    } finally {
      setInFlight(serviceKey, false);
    }
  }, [errorText]);

  const testAll = useCallback(async () => {
    counter.current += 1;
    const token = counter.current;
    setTestingAll(true);
    setError(null);
    try {
      const list = await settingsApi.testAllApiKeys();
      list.forEach((result) => applyIfNewest(result.service, token, result));
    } catch (err) {
      setError(errorText(err));
    } finally {
      setTestingAll(false);
    }
  }, [errorText]);

  return { results, testing, testingAll, error, testService, testAll };
}
