import { useState, useEffect, useCallback } from 'react';
import { emailSearchApi } from '../../services/api/emailSearchApi';
import { createLogger } from '../../../../core/utils/logger';

const logger = createLogger('EmailSearchSettingsApi');

const DEFAULT_CONFIG = {
  timeout_seconds: 10,
  max_concurrency: 10,
  proxy_url: '',
  use_tor: false,
  enable_smtp_checks: false,
  enable_headless_checks: false,
  latest_pypi_version: null,
  pypi_checked_at: null,
};

export function useEmailSearchSettings() {
  const [config, setConfig] = useState(DEFAULT_CONFIG);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    let ignore = false;

    const load = async () => {
      try {
        setLoading(true);
        const data = await emailSearchApi.getConfig();
        if (!ignore) setConfig(data);
      } catch (err) {
        if (!ignore) {
          setError(err);
          logger.error('Settings error:', err);
        }
      } finally {
        if (!ignore) setLoading(false);
      }
    };

    load();
    return () => { ignore = true; };
  }, []);

  const updateConfig = useCallback(async (updates) => {
    if (saving) return { success: false };

    try {
      setSaving(true);
      setError(null);
      const newConfig = await emailSearchApi.updateConfig({ ...config, ...updates });
      setConfig(newConfig);
      return { success: true };
    } catch (err) {
      setError(err);
      return { success: false, error: err };
    } finally {
      setSaving(false);
    }
  }, [config, saving]);

  const setConfigDirect = useCallback((newConfig) => setConfig(newConfig), []);

  return { config, loading, saving, error, updateConfig, setConfig: setConfigDirect };
}
