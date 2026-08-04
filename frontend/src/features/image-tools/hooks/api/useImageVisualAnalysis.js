import { useState } from 'react';
import { imageVisualAnalysisApi } from '../../services/api/imageVisualAnalysisApi';
import { createLogger } from '../../../../core/utils/logger';

const logger = createLogger('ImageVisualAnalysis');

export function useImageVisualAnalysis() {
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const analyzeVisuals = async (file) => {
    setLoading(true);
    setError(null);
    try {
      const visualResult = await imageVisualAnalysisApi.analyzeVisuals(file);
      setResult(visualResult);
    } catch (err) {
      logger.error('Error running visual analysis:', err);
      setError(err.response?.data?.detail || err.message || 'Failed to run visual analysis');
    }
    setLoading(false);
  };

  return { result, loading, error, analyzeVisuals };
}
