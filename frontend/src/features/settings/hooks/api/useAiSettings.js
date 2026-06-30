import { useState, useEffect, useCallback } from 'react';
import { useSetAtom } from 'jotai';
import { useTranslation } from 'react-i18next';
import { aiSettingsState } from '../../../../core/state/atoms';
import { settingsApi } from '../../services/api/settingsApi';

export function useAiSettings() {
  const { t } = useTranslation('settings');
  const [loading, setLoading] = useState(false);
  const [availableModels, setAvailableModels] = useState([]);
  const setAiSettings = useSetAtom(aiSettingsState);

  useEffect(() => {
    settingsApi.getAvailableModels()
      .then(data => setAvailableModels(data.models || []))
      .catch(() => setAvailableModels([]));
  }, []);

  const updateAiSettings = useCallback(async (settings) => {
    setLoading(true);
    try {
      const updated = await settingsApi.updateAiSettings(settings);
      setAiSettings(updated);
      return { success: true, message: t('notifications.aiSettingsUpdated') };
    } catch (err) {
      const errorMessage = err.response?.data?.detail || t('notifications.saveError');
      return { success: false, message: errorMessage };
    } finally {
      setLoading(false);
    }
  }, [setAiSettings, t]);

  return { loading, availableModels, updateAiSettings };
}
