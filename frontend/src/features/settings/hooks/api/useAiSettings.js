import { useState, useEffect, useCallback } from 'react';
import { useSetAtom } from 'jotai';
import { aiSettingsState } from '../../../../core/state/atoms';
import { settingsApi } from '../../services/api/settingsApi';
import { NOTIFICATION_MESSAGES } from '../../constants/settingsConstants';

export function useAiSettings() {
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
      return { success: true, message: 'AI settings updated successfully.' };
    } catch (err) {
      const errorMessage = err.response?.data?.detail || NOTIFICATION_MESSAGES.SAVE_ERROR;
      return { success: false, message: errorMessage };
    } finally {
      setLoading(false);
    }
  }, [setAiSettings]);

  return { loading, availableModels, updateAiSettings };
}
