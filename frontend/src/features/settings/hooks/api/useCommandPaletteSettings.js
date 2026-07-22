import { useState, useCallback } from 'react';
import { useSetAtom } from 'jotai';
import { generalSettingsState } from '../../../../core/state/atoms';
import { settingsApi } from '../../services/api/settingsApi';
import { NOTIFICATION_MESSAGES } from '../../constants/settingsConstants';

/**
 * Hook for the command palette settings group (Settings → Управление) — auto-open,
 * start screen, always-tiles. Same shape as useGeneralSettings.js's darkmode/language hooks.
 */
export function useCommandPaletteSettings() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const setGeneralSettings = useSetAtom(generalSettingsState);

  const updateCommandPaletteSettings = useCallback(async (updates) => {
    setLoading(true);
    setError(null);
    try {
      const response = await settingsApi.updateCommandPaletteSettings(updates);
      setGeneralSettings((prev) => ({ ...prev, ...response }));
      return { success: true, message: NOTIFICATION_MESSAGES.COMMAND_PALETTE_UPDATED };
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
    updateCommandPaletteSettings,
  };
}
