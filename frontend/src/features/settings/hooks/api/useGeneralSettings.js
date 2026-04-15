import { useState, useCallback } from 'react';
import { useSetAtom } from 'jotai';
import { generalSettingsState } from '../../../../core/state/atoms';
import { settingsApi } from '../../services/api/settingsApi';
import { NOTIFICATION_MESSAGES } from '../../constants/settingsConstants';

/**
 * Hook for general settings API operations
 */
export function useGeneralSettings() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const setGeneralSettings = useSetAtom(generalSettingsState);

  const updateFont = useCallback(async (font) => {
    setLoading(true);
    setError(null);
    try {
      await settingsApi.updateFont(font);
      setGeneralSettings(prev => ({ ...prev, font }));
      document.body.setAttribute('data-font', font);
      return { success: true, message: NOTIFICATION_MESSAGES.FONT_UPDATED };
    } catch (err) {
      const errorMessage = err.response?.data?.detail || NOTIFICATION_MESSAGES.SAVE_ERROR;
      setError(errorMessage);
      return { success: false, message: errorMessage };
    } finally {
      setLoading(false);
    }
  }, [setGeneralSettings]);

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

  return {
    loading,
    error,
    updateFont,
    updateDarkmode,
  };
}
