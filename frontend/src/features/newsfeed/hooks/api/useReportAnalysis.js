import { useState, useRef, useCallback, useEffect } from 'react';
import { getStreamUrl } from '../../utils/urlUtils';
import { createLogger } from '../../../../core/utils/logger';

const logger = createLogger('ReportAnalysis');

export function useReportAnalysis() {
  const [step, setStep] = useState(0);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);
  const [infoMessage, setInfoMessage] = useState(null);
  const [ranking, setRanking] = useState([]);
  const [analysisResults, setAnalysisResults] = useState([]);
  const eventSourceRef = useRef(null);

  useEffect(() => {
    return () => {
      if (eventSourceRef.current) {
        eventSourceRef.current.close();
        eventSourceRef.current = null;
      }
    };
  }, []);

  const showStopButton = step >= 1 && step < 5;

  const startAnalysis = useCallback(() => {
    setStep(1);
    setIsLoading(true);
    setError(null);
    setInfoMessage(null);
    setRanking([]);
    setAnalysisResults([]);

    const url = getStreamUrl();
    const es = new EventSource(url);
    eventSourceRef.current = es;

    es.onmessage = (event) => {
      const rawData = event.data;
      if (!rawData || !rawData.trim()) return;

      try {
        const parsed = JSON.parse(rawData);

        switch (parsed.type) {
          case 'ranking':
            setStep(3);
            setRanking(parsed.articles || []);
            if (parsed.info) setInfoMessage(parsed.info);
            break;
          case 'analysis':
            setStep(4);
            if (parsed.article_result) {
              setAnalysisResults(prev => [...prev, parsed.article_result]);
            }
            break;
          case 'complete':
            setStep(5);
            setIsLoading(false);
            setInfoMessage(parsed.message);
            es.close();
            eventSourceRef.current = null;
            break;
          default:
            break;
        }
      } catch (err) {
        logger.error('SSE parse error:', err);
      }
    };

    es.onerror = () => {
      setError('An error occurred while streaming data.');
      setIsLoading(false);
      setStep(0);
      if (eventSourceRef.current) {
        eventSourceRef.current.close();
        eventSourceRef.current = null;
      }
    };
  }, []);

  const stopAnalysis = useCallback(() => {
    if (eventSourceRef.current) {
      eventSourceRef.current.close();
      eventSourceRef.current = null;
    }
    setStep(0);
    setIsLoading(false);
    setInfoMessage('Analysis stream stopped by user.');
  }, []);

  return {
    step,
    isLoading,
    error,
    infoMessage,
    ranking,
    analysisResults,
    showStopButton,
    startAnalysis,
    stopAnalysis,
  };
}
