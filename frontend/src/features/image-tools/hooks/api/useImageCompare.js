import { useState } from 'react';
import { imageCompareApi } from '../../services/api/imageCompareApi';
import { createLogger } from '../../../../core/utils/logger';

const logger = createLogger('ImageCompare');

export function useImageCompare() {
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const compareImages = async (fileLeft, fileRight) => {
    setLoading(true);
    setError(null);
    try {
      const compareResult = await imageCompareApi.compareImages(fileLeft, fileRight);
      setResult(compareResult);
    } catch (err) {
      logger.error('Error comparing images:', err);
      setError(err.response?.data?.detail || err.message || 'Failed to compare images');
    }
    setLoading(false);
  };

  return { result, loading, error, compareImages };
}
