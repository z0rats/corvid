import { useCallback } from 'react';
import { useRemoteConfig } from '../../../../core/hooks/useRemoteConfig';
import { newsfeedSettingsApi } from '../../services/api/settingsApi';
import { DEFAULT_CONFIG, SETTINGS } from '../../constants/newsfeedConstants';

export function useNewsfeedSettings() {
  const remote = useRemoteConfig(newsfeedSettingsApi.getConfig, newsfeedSettingsApi.updateConfig, DEFAULT_CONFIG);

  const updateConfig = useCallback(async (updates) => {
    const merged = { ...remote.config, ...updates };

    try {
      if (merged.fetch_interval_minutes < SETTINGS.MIN_FETCH_INTERVAL) {
        throw new Error(`Fetch interval must be at least ${SETTINGS.MIN_FETCH_INTERVAL} minutes`);
      }
      if (merged.fetch_interval_minutes > SETTINGS.MAX_FETCH_INTERVAL) {
        throw new Error(`Fetch interval must be at most ${SETTINGS.MAX_FETCH_INTERVAL} minutes`);
      }
      if (merged.retention_days < SETTINGS.MIN_RETENTION_DAYS) {
        throw new Error(`Retention period must be at least ${SETTINGS.MIN_RETENTION_DAYS} days`);
      }
    } catch (err) {
      return { success: false, error: err };
    }

    return remote.updateConfig(updates);
  }, [remote]);

  return { ...remote, updateConfig };
}
