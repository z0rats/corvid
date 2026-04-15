import { useState, useCallback, useEffect, useMemo } from 'react';
import { iocLookupApi } from '../../../../shared/services/api/iocLookupApi';
import { createLogger } from '../../../../../../core/utils/logger';

const logger = createLogger('BulkLookupSettings');

function buildSettingsList(dbKeyStatusMap, serviceDefinitions) {
  const availableServices = Object.entries(serviceDefinitions)
    .filter(([_, config]) => config.isAvailable)
    .reduce((acc, [key, config]) => {
      acc[key] = config;
      return acc;
    }, {});

  return Object.keys(availableServices).map(serviceKey => {
    const serviceDef = availableServices[serviceKey];
    const requiredKeys = serviceDef.requiredKeys || [];

    let isEnabled;
    if (requiredKeys.length === 0) {
      isEnabled = dbKeyStatusMap[serviceKey] === true;
    } else {
      isEnabled = requiredKeys.every(keyName => dbKeyStatusMap[keyName] === true);
    }

    return {
      name: serviceKey,
      is_bulk_lookup_enabled: isEnabled
    };
  });
}

export function useBulkLookupSettings(serviceDefinitions, serviceDefsLoading) {
  const [initialLoading, setInitialLoading] = useState(true);
  const [serviceSettings, setServiceSettings] = useState([]);
  const [settingsError, setSettingsError] = useState('');

  const fetchServiceStatuses = useCallback(async () => {
    if (serviceDefsLoading || Object.keys(serviceDefinitions).length === 0) {
      return;
    }

    try {
      const dbKeyStatusMap = await iocLookupApi.fetchBulkLookupSettings();
      setServiceSettings(buildSettingsList(dbKeyStatusMap, serviceDefinitions));
    } catch (error) {
      logger.error('Failed to fetch bulk IOC lookup settings:', error);
      setSettingsError('Could not load settings for bulk lookup services.');
    } finally {
      setInitialLoading(false);
    }
  }, [serviceDefinitions, serviceDefsLoading]);

  useEffect(() => {
    let ignore = false;

    const load = async () => {
      if (serviceDefsLoading || Object.keys(serviceDefinitions).length === 0) {
        return;
      }

      try {
        const dbKeyStatusMap = await iocLookupApi.fetchBulkLookupSettings();
        if (ignore) return;
        setServiceSettings(buildSettingsList(dbKeyStatusMap, serviceDefinitions));
      } catch (error) {
        if (!ignore) {
          logger.error('Failed to fetch bulk IOC lookup settings:', error);
          setSettingsError('Could not load settings for bulk lookup services.');
        }
      } finally {
        if (!ignore) setInitialLoading(false);
      }
    };

    load();
    return () => { ignore = true; };
  }, [serviceDefinitions, serviceDefsLoading]);

  const hasEnabledServices = useMemo(() => {
    return serviceSettings.some(s => s.is_bulk_lookup_enabled);
  }, [serviceSettings]);

  const enabledServiceNames = useMemo(() => {
    return serviceSettings
      .filter(s => s.is_bulk_lookup_enabled)
      .map(s => s.name);
  }, [serviceSettings]);

  return {
    loadingSettings: initialLoading,
    serviceSettings,
    settingsError,
    setSettingsError,
    hasEnabledServices,
    enabledServiceNames,
    refreshSettings: fetchServiceStatuses,
  };
}
