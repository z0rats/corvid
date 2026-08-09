import { useCallback } from 'react';
import { useSetAtom } from 'jotai';
import { useTranslation } from 'react-i18next';
import { apiKeysState } from '../../../../core/state/atoms';
import { settingsApi } from '../../services/api/settingsApi';
import { useSettingsMutation } from '../../../../core/hooks/useSettingsMutation';
import { createLogger } from '../../../../core/utils/logger';

const logger = createLogger('ApiKeys');

/**
 * Hook for API keys operations
 */
export function useApiKeys() {
  const { t } = useTranslation('settings');
  const { loading, error, run } = useSettingsMutation();
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

  const getServicesConfig = useCallback(() => run(async () => {
    const config = await settingsApi.getServicesConfig();
    return { data: config };
  }, t('notifications.loadError')), [run, t]);

  const getKeyStatus = useCallback((keyName, relatedKeys = []) => run(async () => {
    const [configuredResponse, activeResponse] = await Promise.all([
      settingsApi.getConfiguredApiKeys(),
      settingsApi.getActiveApiKeys(),
    ]);

    const primaryKeyExists = configuredResponse[keyName] || false;
    const allKeysAssociatedWithService = [keyName, ...relatedKeys];
    const serviceIsActive = allKeysAssociatedWithService.some(key => activeResponse[key]);

    return {
      data: {
        existsInBackend: primaryKeyExists,
        isServiceActive: serviceIsActive,
      },
    };
  }, t('notifications.loadError')), [run, t]);

  const saveApiKey = useCallback((name, key) => run(async () => {
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
    return { message: t('notifications.apiKeySaved') };
  }, t('notifications.saveError')), [run, refreshApiKeys, t]);

  const deleteApiKey = useCallback((name) => run(async () => {
    await settingsApi.updateApiKey(name, '', false, false);
    await refreshApiKeys();
    return { message: t('notifications.apiKeyRemoved') };
  }, t('notifications.saveError')), [run, refreshApiKeys, t]);

  const toggleServiceActivation = useCallback((keyNames, currentStatus, serviceName) => run(async () => {
    const targetIsActive = !currentStatus;

    await Promise.all(
      keyNames.map(keyName => settingsApi.updateApiKeyStatus(keyName, targetIsActive))
    );

    await refreshApiKeys();
    const message = targetIsActive
      ? t('notifications.serviceActivated', { service: serviceName })
      : t('notifications.serviceDeactivated', { service: serviceName });

    return { message, isActive: targetIsActive };
  }, t('notifications.saveError')), [run, refreshApiKeys, t]);

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
