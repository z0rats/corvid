import { useState, useEffect, useCallback } from 'react';
import { newsfeedSettingsApi } from '../../services/api/settingsApi';
import { DEFAULT_CONFIG, SETTINGS } from '../../constants/newsfeedConstants';
import { createLogger } from '../../../../core/utils/logger';

const logger = createLogger('NewsfeedSettingsApi');

export function useNewsfeedSettings() {
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [config, setConfig] = useState(DEFAULT_CONFIG);
  const [error, setError] = useState(null);

  const fetchConfig = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const response = await newsfeedSettingsApi.getConfig();
      setConfig(response);
    } catch (err) {
      setError(err);
      logger.error('Settings error:', err);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    let ignore = false;

    const load = async () => {
      try {
        setLoading(true);
        setError(null);
        const response = await newsfeedSettingsApi.getConfig();
        if (!ignore) setConfig(response);
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
    if (saving) return;

    try {
      setSaving(true);
      setError(null);
      const newConfig = { ...config, ...updates };

      if (newConfig.fetch_interval_minutes < SETTINGS.MIN_FETCH_INTERVAL) {
        throw new Error(`Fetch interval must be at least ${SETTINGS.MIN_FETCH_INTERVAL} minutes`);
      }
      if (newConfig.fetch_interval_minutes > SETTINGS.MAX_FETCH_INTERVAL) {
        throw new Error(`Fetch interval must be at most ${SETTINGS.MAX_FETCH_INTERVAL} minutes`);
      }
      if (newConfig.retention_days < SETTINGS.MIN_RETENTION_DAYS) {
        throw new Error(`Retention period must be at least ${SETTINGS.MIN_RETENTION_DAYS} days`);
      }

      const response = await newsfeedSettingsApi.updateConfig(newConfig);
      setConfig(response);
      return { success: true };
    } catch (err) {
      setError(err);
      setConfig((prev) => ({ ...prev }));
      return { success: false, error: err };
    } finally {
      setSaving(false);
    }
  }, [config, saving]);

  return {
    config,
    loading,
    saving,
    error,
    updateConfig,
    fetchConfig,
  };
}
