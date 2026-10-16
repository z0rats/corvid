import { useState, useEffect, useCallback } from 'react';
import { useAtomValue, useSetAtom } from 'jotai';
import { useTranslation } from 'react-i18next';
import { aiSettingsState, availableLlmModelsState } from '../../../../core/state/atoms';
import { requestLlmModelsReprobe } from '../../../../core/utils/llmModelsReprobe';
import { settingsApi } from '../../services/api/settingsApi';

export function useAiSettings() {
  const { t } = useTranslation('settings');
  const [loading, setLoading] = useState(false);
  // The app-wide registry list (core/hooks/api/useAppSettings), refreshed on open so a model
  // started or a key saved elsewhere shows up here too - one source of truth, not a local copy.
  const availableModels = useAtomValue(availableLlmModelsState);
  const setAiSettings = useSetAtom(aiSettingsState);

  useEffect(() => {
    requestLlmModelsReprobe();
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
