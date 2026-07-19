import { useState, useCallback } from 'react';
import { useSetAtom } from 'jotai';
import { generalSettingsState } from '../../../../core/state/atoms';
import { settingsApi } from '../../services/api/settingsApi';
import { NOTIFICATION_MESSAGES } from '../../constants/settingsConstants';
import i18n from '../../../../core/i18n';

/**
 * Hook for general settings API operations
 */
export function useGeneralSettings() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const setGeneralSettings = useSetAtom(generalSettingsState);

  const updateDarkmode = useCallback(async (darkmode) => {
    setLoading(true);
    setError(null);
    try {
      await settingsApi.updateDarkmode(darkmode);
      setGeneralSettings(prev => ({ ...prev, darkmode }));
      return { success: true, message: NOTIFICATION_MESSAGES.DARKMODE_UPDATED };
    } catch (err) {
      const errorMessage = err.response?.data?.detail || NOTIFICATION_MESSAGES.SAVE_ERROR;
      setError(errorMessage);
      return { success: false, message: errorMessage };
    } finally {
      setLoading(false);
    }
  }, [setGeneralSettings]);

  const updateLanguage = useCallback(async (language) => {
    setLoading(true);
    setError(null);
    try {
      await settingsApi.updateLanguage(language);
      setGeneralSettings(prev => ({ ...prev, language }));
      await i18n.changeLanguage(language);
      return { success: true, message: NOTIFICATION_MESSAGES.LANGUAGE_UPDATED };
    } catch (err) {
      const errorMessage = err.response?.data?.detail || NOTIFICATION_MESSAGES.SAVE_ERROR;
      setError(errorMessage);
      return { success: false, message: errorMessage };
    } finally {
      setLoading(false);
    }
  }, [setGeneralSettings]);

  return {
    loading,
    error,
    updateDarkmode,
    updateLanguage,
  };
}
