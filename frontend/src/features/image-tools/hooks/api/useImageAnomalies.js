import { useState } from 'react';
import { imageAnomalyApi } from '../../services/api/imageAnomalyApi';
import { createLogger } from '../../../../core/utils/logger';

const logger = createLogger('ImageAnomalies');

export function useImageAnomalies() {
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const analyzeAnomalies = async (file) => {
    setLoading(true);
    setError(null);
    try {
      const anomalyResult = await imageAnomalyApi.analyzeAnomalies(file);
      setResult(anomalyResult);
    } catch (err) {
      logger.error('Error running anomaly detection:', err);
      setError(err.response?.data?.detail || err.message || 'Failed to run anomaly detection');
    }
    setLoading(false);
  };

  return { result, loading, error, analyzeAnomalies };
}
