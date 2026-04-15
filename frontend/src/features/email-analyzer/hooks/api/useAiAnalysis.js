import { useState } from 'react';
import { useAtomValue } from 'jotai';
import { hasLlmKeyAtom } from '../../../../core/state/atoms';
import { aiAssistantApi } from '../../services/api/aiAssistantApi';
import { createLogger } from '../../../../core/utils/logger';

const logger = createLogger('AiAnalysis');

export function useAiAnalysis() {
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const hasLlmKey = useAtomValue(hasLlmKeyAtom);

  const analyzeMailBody = async (input) => {
    setLoading(true);
    try {
      const analysisResult = await aiAssistantApi.analyzeMailBody(input);
      setResult(analysisResult);
    } catch (error) {
      logger.error('Error analyzing mail body:', error);
    }
    setLoading(false);
  };

  return { result, loading, hasLlmKey, analyzeMailBody };
}
