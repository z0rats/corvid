import { useCallback } from 'react';
import { useSetAtom } from 'jotai';
import { generalSettingsState } from '../../../../core/state/atoms';
import { settingsApi } from '../../services/api/settingsApi';
import { useSettingsMutation } from '../../../../core/hooks/useSettingsMutation';
import { NOTIFICATION_MESSAGES } from '../../constants/settingsConstants';
import i18n from '../../../../core/i18n';

/**
 * Hook for general settings API operations
 */
export function useGeneralSettings() {
  const { loading, error, run } = useSettingsMutation();
  const setGeneralSettings = useSetAtom(generalSettingsState);

  const updateDarkmode = useCallback((darkmode) => run(async () => {
    await settingsApi.updateDarkmode(darkmode);
    setGeneralSettings(prev => ({ ...prev, darkmode }));
    return { message: NOTIFICATION_MESSAGES.DARKMODE_UPDATED };
  }, NOTIFICATION_MESSAGES.SAVE_ERROR), [run, setGeneralSettings]);

  const updateLanguage = useCallback((language) => run(async () => {
    await settingsApi.updateLanguage(language);
    setGeneralSettings(prev => ({ ...prev, language }));
    await i18n.changeLanguage(language);
    return { message: NOTIFICATION_MESSAGES.LANGUAGE_UPDATED };
  }, NOTIFICATION_MESSAGES.SAVE_ERROR), [run, setGeneralSettings]);

  return {
    loading,
    error,
    updateDarkmode,
    updateLanguage,
  };
}
