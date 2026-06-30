import { useState, useCallback } from 'react';
import { useSetAtom } from 'jotai';
import { useTranslation } from 'react-i18next';
import { modulesState } from '../../../../core/state/atoms';
import { settingsApi } from '../../services/api/settingsApi';

/**
 * Hook for modules operations
 */
export function useModules() {
  const { t } = useTranslation('settings');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const setModules = useSetAtom(modulesState);

  const toggleModule = useCallback(async (moduleName, currentEnabled) => {
    setLoading(true);
    setError(null);
    try {
      const newEnabledStatus = !currentEnabled;
      await settingsApi.updateModuleStatus(moduleName, newEnabledStatus);

      setModules(prev => ({
        ...prev,
        [moduleName]: { ...prev[moduleName], enabled: newEnabledStatus },
      }));

      const message = newEnabledStatus
        ? t('notifications.moduleEnabled')
        : t('notifications.moduleDisabled');

      return { success: true, message };
    } catch (err) {
      const errorMessage = err.response?.data?.detail || t('notifications.saveError');
      setError(errorMessage);
      return { success: false, message: errorMessage };
    } finally {
      setLoading(false);
    }
  }, [setModules, t]);

  return {
    loading,
    error,
    toggleModule,
  };
}
