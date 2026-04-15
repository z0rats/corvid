import { useEffect, useState, useCallback, useRef } from 'react';
import { useSetAtom } from 'jotai';
import { healthService } from '../../services/api/healthService';
import { appVersionAtom } from '../../state/atoms';
import { createLogger } from '../../utils/logger';

const logger = createLogger('HealthCheck');

export function useHealthCheck() {
  const [status, setStatus] = useState('loading');
  const setAppVersion = useSetAtom(appVersionAtom);

  const checkBackendHealth = useCallback(async (isBackgroundCheck = false) => {
    try {
      if (!isBackgroundCheck) {
        setStatus('loading');
      }

      const response = await healthService.checkBackendHealth();

      if (response.status === 'ok') {
        setStatus('healthy');
        if (response.version) {
          setAppVersion(response.version);
        }
      } else {
        setStatus('error');
      }
    } catch (error) {
      logger.error('Backend health check failed:', error);
      setStatus('error');
    }
  }, [setAppVersion]);

  const checkHealthRef = useRef(checkBackendHealth);
  checkHealthRef.current = checkBackendHealth;

  useEffect(() => {
    checkHealthRef.current(false);

    const healthCheckInterval = setInterval(() => {
      checkHealthRef.current(true);
    }, 300000);

    return () => clearInterval(healthCheckInterval);
  }, []);

  const handleRetry = () => {
    checkBackendHealth(false);
  };

  return {
    status,
    handleRetry
  };
}
