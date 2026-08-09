import { useCallback } from 'react';
import { useSetAtom } from 'jotai';
import { generalSettingsState } from '../../../../core/state/atoms';
import { settingsApi } from '../../services/api/settingsApi';
import { useSettingsMutation } from '../../../../core/hooks/useSettingsMutation';
import { NOTIFICATION_MESSAGES } from '../../constants/settingsConstants';

/**
 * Hook for the command palette settings group (Settings → Управление) — auto-open,
 * start screen, always-tiles. Same shape as useGeneralSettings.js's darkmode/language hooks.
 */
export function useCommandPaletteSettings() {
  const { loading, error, run } = useSettingsMutation();
  const setGeneralSettings = useSetAtom(generalSettingsState);

  const updateCommandPaletteSettings = useCallback((updates) => run(async () => {
    const response = await settingsApi.updateCommandPaletteSettings(updates);
    setGeneralSettings((prev) => ({ ...prev, ...response }));
    return { message: NOTIFICATION_MESSAGES.COMMAND_PALETTE_UPDATED };
  }, NOTIFICATION_MESSAGES.SAVE_ERROR), [run, setGeneralSettings]);

  return {
    loading,
    error,
    updateCommandPaletteSettings,
  };
}
