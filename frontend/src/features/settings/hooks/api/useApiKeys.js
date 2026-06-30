import { useState, useCallback } from 'react';
import { useSetAtom } from 'jotai';
import { useTranslation } from 'react-i18next';
import { apiKeysState } from '../../../../core/state/atoms';
import { settingsApi } from '../../services/api/settingsApi';
import { createLogger } from '../../../../core/utils/logger';

const logger = createLogger('ApiKeys');

/**
 * Hook for API keys operations
 */
export function useApiKeys() {
  const { t } = useTranslation('settings');
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
      const errorMessage = err.response?.data?.detail || t('notifications.loadError');
      setError(errorMessage);
      return { success: false, message: errorMessage };
    } finally {
      setLoading(false);
    }
  }, [t]);

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
      const errorMessage = err.response?.data?.detail || t('notifications.loadError');
      setError(errorMessage);
      return { success: false, message: errorMessage };
    } finally {
      setLoading(false);
    }
  }, [t]);

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
      return { success: true, message: t('notifications.apiKeySaved') };
    } catch (err) {
      const errorMessage = err.response?.data?.detail || t('notifications.saveError');
      setError(errorMessage);
      return { success: false, message: errorMessage };
    } finally {
      setLoading(false);
    }
  }, [refreshApiKeys, t]);

  const deleteApiKey = useCallback(async (name) => {
    setLoading(true);
    setError(null);
    try {
      await settingsApi.updateApiKey(name, '', false, false);
      await refreshApiKeys();
      return { success: true, message: t('notifications.apiKeyRemoved') };
    } catch (err) {
      const errorMessage = err.response?.data?.detail || t('notifications.saveError');
      setError(errorMessage);
      return { success: false, message: errorMessage };
    } finally {
      setLoading(false);
    }
  }, [refreshApiKeys, t]);

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
        ? t('notifications.serviceActivated', { service: serviceName })
        : t('notifications.serviceDeactivated', { service: serviceName });

      return { success: true, message, isActive: targetIsActive };
    } catch (err) {
      const errorMessage = err.response?.data?.detail || t('notifications.saveError');
      setError(errorMessage);
      return { success: false, message: errorMessage };
    } finally {
      setLoading(false);
    }
  }, [refreshApiKeys, t]);

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
