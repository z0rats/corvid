import { useState, useCallback } from 'react';
import { useSetAtom } from 'jotai';
import { modulesState } from '../../../../core/state/atoms';
import { settingsApi } from '../../services/api/settingsApi';
import { NOTIFICATION_MESSAGES } from '../../constants/settingsConstants';

/**
 * Hook for modules operations
 */
export function useModules() {
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
        ? NOTIFICATION_MESSAGES.MODULE_ENABLED
        : NOTIFICATION_MESSAGES.MODULE_DISABLED;

      return { success: true, message };
    } catch (err) {
      const errorMessage = err.response?.data?.detail || NOTIFICATION_MESSAGES.SAVE_ERROR;
      setError(errorMessage);
      return { success: false, message: errorMessage };
    } finally {
      setLoading(false);
    }
  }, [setModules]);

  return {
    loading,
    error,
    toggleModule,
  };
}
