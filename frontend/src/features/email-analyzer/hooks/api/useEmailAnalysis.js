import { useState, useRef, useEffect, useCallback } from 'react';
import { useTranslation } from 'react-i18next';
import { emailAnalyzerApi } from '../../services/api/emailAnalyzerApi';

export function useEmailAnalysis() {
  const { t } = useTranslation('emailAnalyzer');
  const [result, setResult] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);
  const [uploadProgress, setUploadProgress] = useState(0);
  const progressIntervalRef = useRef(null);
  const completionTimeoutRef = useRef(null);
  const abortControllerRef = useRef(null);

  useEffect(() => {
    return () => {
      clearInterval(progressIntervalRef.current);
      clearTimeout(completionTimeoutRef.current);
      abortControllerRef.current?.abort();
    };
  }, []);

  const analyzeEmail = useCallback(async (file) => {
    if (!file) {
      setError(t('errors.noFileProvided'));
      return;
    }

    abortControllerRef.current?.abort();
    abortControllerRef.current = new AbortController();
    const { signal } = abortControllerRef.current;

    try {
      setIsLoading(true);
      setError(null);
      setUploadProgress(0);

      progressIntervalRef.current = setInterval(() => {
        setUploadProgress(prev => {
          if (prev >= 90) {
            clearInterval(progressIntervalRef.current);
            return prev;
          }
          return prev + 10;
        });
      }, 200);

      const analysisResult = await emailAnalyzerApi.analyzeEmail(file);

      if (signal.aborted) return;

      clearInterval(progressIntervalRef.current);
      setUploadProgress(100);

      completionTimeoutRef.current = setTimeout(() => {
        if (signal.aborted) return;
        setResult(analysisResult);
        setUploadProgress(0);
        setIsLoading(false);
      }, 300);

    } catch (err) {
      if (signal.aborted) return;
      clearInterval(progressIntervalRef.current);
      setError(err.response?.data?.detail || err.message || t('errors.analysisFailed'));
      setUploadProgress(0);
      setIsLoading(false);
    }
  }, [t]);

  const reset = useCallback(() => {
    abortControllerRef.current?.abort();
    setResult(null);
    setError(null);
    setUploadProgress(0);
    setIsLoading(false);
  }, []);

  return {
    result,
    isLoading,
    error,
    uploadProgress,
    analyzeEmail,
    reset
  };
}
