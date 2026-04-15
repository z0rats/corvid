import { useState, useEffect, useCallback, useMemo } from 'react';
import { useAtomValue } from 'jotai';
import { apiKeyAvailabilityAtom } from '../../../../../core/state/atoms';
import { iocLookupApi } from '../../../shared/services/api/iocLookupApi';
import { createLogger } from '../../../../../core/utils/logger';

const logger = createLogger('ServiceDefinitions');

export function useServiceDefinitions() {
  const [serviceDefinitions, setServiceDefinitions] = useState({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [refreshKey, setRefreshKey] = useState(0);
  const apiKeyAvailability = useAtomValue(apiKeyAvailabilityAtom);

  const refetch = useCallback(() => setRefreshKey(prev => prev + 1), []);

  useEffect(() => {
    let ignore = false;

    const fetch = async () => {
      try {
        setLoading(true);
        setError(null);
        const definitions = await iocLookupApi.fetchServiceDefinitions();
        if (!ignore) {
          setServiceDefinitions(definitions);
        }
      } catch (err) {
        if (!ignore) {
          logger.error('Failed to fetch service definitions:', err);
          setError('Failed to load service definitions');
        }
      } finally {
        if (!ignore) {
          setLoading(false);
        }
      }
    };

    fetch();
    return () => { ignore = true; };
  }, [apiKeyAvailability, refreshKey]);

  const availableServices = useMemo(() => {
    return Object.entries(serviceDefinitions)
      .filter(([_, config]) => config.isAvailable)
      .reduce((acc, [key, config]) => {
        acc[key] = config;
        return acc;
      }, {});
  }, [serviceDefinitions]);

  const isServiceAvailable = useCallback((serviceName) => {
    return serviceDefinitions[serviceName]?.isAvailable || false;
  }, [serviceDefinitions]);

  return {
    serviceDefinitions,
    loading,
    error,
    refetch,
    availableServices,
    isServiceAvailable,
  };
}
