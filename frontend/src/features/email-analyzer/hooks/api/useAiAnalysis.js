import { useState } from 'react';
import { useAtomValue } from 'jotai';
import { llmAvailableAtom } from '../../../../core/state/atoms';
import { aiAssistantApi } from '../../services/api/aiAssistantApi';
import { createLogger } from '../../../../core/utils/logger';

const logger = createLogger('AiAnalysis');

export function useAiAnalysis() {
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(false);
  const llmAvailable = useAtomValue(llmAvailableAtom);

  const analyzeMailBody = async (input) => {
    setLoading(true);
    setError(false);
    try {
      const analysisResult = await aiAssistantApi.analyzeMailBody(input);
      setResult(analysisResult);
    } catch (err) {
      logger.error('Error analyzing mail body:', err);
      // Drop the previous answer so it can't read as the result of this failed run.
      setResult(null);
      setError(true);
    }
    setLoading(false);
  };

  return { result, loading, error, llmAvailable, analyzeMailBody };
}
