import { useState, useCallback } from 'react';
import { useSetAtom } from 'jotai';
import { apiKeysState } from '../../../../core/state/atoms';
import { settingsApi } from '../../services/api/settingsApi';
import { NOTIFICATION_MESSAGES } from '../../constants/settingsConstants';
import { createLogger } from '../../../../core/utils/logger';

const logger = createLogger('ApiKeys');

/**
 * Hook for API keys operations
 */
export function useApiKeys() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const setApiKeys = useSetAtom(apiKeysState);

  const refreshApiKeys = useCallback(async () => {
    try {
      const activeKeys = await settingsApi.getActiveApiKeys();
      setApiKeys(activeKeys);
      return activeKeys;
    } catch (err) {
      logger.error('Error refreshing API keys:', err);
      throw err;
    }
  }, [setApiKeys]);

  const getServicesConfig = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const config = await settingsApi.getServicesConfig();
      return { success: true, data: config };
    } catch (err) {
      const errorMessage = err.response?.data?.detail || NOTIFICATION_MESSAGES.LOAD_ERROR;
      setError(errorMessage);
      return { success: false, message: errorMessage };
    } finally {
      setLoading(false);
    }
  }, []);

  const getKeyStatus = useCallback(async (keyName, relatedKeys = []) => {
    setLoading(true);
    setError(null);
    try {
      const [configuredResponse, activeResponse] = await Promise.all([
        settingsApi.getConfiguredApiKeys(),
        settingsApi.getActiveApiKeys(),
      ]);

      const primaryKeyExists = configuredResponse[keyName] || false;
      const allKeysAssociatedWithService = [keyName, ...relatedKeys];
      const serviceIsActive = allKeysAssociatedWithService.some(key => activeResponse[key]);

      return {
        success: true,
        data: {
          existsInBackend: primaryKeyExists,
          isServiceActive: serviceIsActive,
        },
      };
    } catch (err) {
      const errorMessage = err.response?.data?.detail || NOTIFICATION_MESSAGES.LOAD_ERROR;
      setError(errorMessage);
      return { success: false, message: errorMessage };
    } finally {
      setLoading(false);
    }
  }, []);

  const saveApiKey = useCallback(async (name, key) => {
    setLoading(true);
    setError(null);
    try {
      try {
        await settingsApi.createApiKey(name, key);
      } catch (err) {
        if (err.response?.status === 409) {
          await settingsApi.updateApiKey(name, key);
        } else {
          throw err;
        }
      }
      await refreshApiKeys();
      return { success: true, message: NOTIFICATION_MESSAGES.API_KEY_SAVED };
    } catch (err) {
      const errorMessage = err.response?.data?.detail || NOTIFICATION_MESSAGES.SAVE_ERROR;
      setError(errorMessage);
      return { success: false, message: errorMessage };
    } finally {
      setLoading(false);
    }
  }, [refreshApiKeys]);

  const deleteApiKey = useCallback(async (name) => {
    setLoading(true);
    setError(null);
    try {
      await settingsApi.updateApiKey(name, '', false, false);
      await refreshApiKeys();
      return { success: true, message: NOTIFICATION_MESSAGES.API_KEY_REMOVED };
    } catch (err) {
      const errorMessage = err.response?.data?.detail || NOTIFICATION_MESSAGES.SAVE_ERROR;
      setError(errorMessage);
      return { success: false, message: errorMessage };
    } finally {
      setLoading(false);
    }
  }, [refreshApiKeys]);

  const toggleServiceActivation = useCallback(async (keyNames, currentStatus, serviceName) => {
    setLoading(true);
    setError(null);
    try {
      const targetIsActive = !currentStatus;

      await Promise.all(
        keyNames.map(keyName => settingsApi.updateApiKeyStatus(keyName, targetIsActive))
      );

      await refreshApiKeys();
      const message = targetIsActive
        ? `${serviceName} ${NOTIFICATION_MESSAGES.API_KEY_ACTIVATED}`
        : `${serviceName} ${NOTIFICATION_MESSAGES.API_KEY_DEACTIVATED}`;

      return { success: true, message, isActive: targetIsActive };
    } catch (err) {
      const errorMessage = err.response?.data?.detail || NOTIFICATION_MESSAGES.SAVE_ERROR;
      setError(errorMessage);
      return { success: false, message: errorMessage };
    } finally {
      setLoading(false);
    }
  }, [refreshApiKeys]);

  return {
    loading,
    error,
    refreshApiKeys,
    getServicesConfig,
    getKeyStatus,
    saveApiKey,
    deleteApiKey,
    toggleServiceActivation,
  };
}
