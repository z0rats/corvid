import { useState, useCallback } from 'react';
import { useTranslation } from 'react-i18next';
import { settingsApi } from '../../services/api/settingsApi';

/**
 * Hook for the API quota/usage dashboard panel
 */
export function useQuota() {
  const { t } = useTranslation('settings');
  const [quotas, setQuotas] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const refreshQuota = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await settingsApi.getQuotaStatus();
      setQuotas(data);
      return { success: true, data };
    } catch (err) {
      const errorMessage = err.response?.data?.detail || t('quota.loadError');
      setError(errorMessage);
      return { success: false, message: errorMessage };
    } finally {
      setLoading(false);
    }
  }, [t]);

  return {
    quotas,
    loading,
    error,
    refreshQuota,
  };
}
