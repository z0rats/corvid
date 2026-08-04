import { useState } from 'react';
import { imageStructureApi } from '../../services/api/imageStructureApi';
import { createLogger } from '../../../../core/utils/logger';

const logger = createLogger('ImageStructure');

export function useImageStructure() {
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const analyzeStructure = async (file) => {
    setLoading(true);
    setError(null);
    try {
      const structureResult = await imageStructureApi.analyzeStructure(file);
      setResult(structureResult);
    } catch (err) {
      logger.error('Error analyzing image structure:', err);
      setError(err.response?.data?.detail || err.message || 'Failed to analyze image structure');
    }
    setLoading(false);
  };

  return { result, loading, error, analyzeStructure };
}
