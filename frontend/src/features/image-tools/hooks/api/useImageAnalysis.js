import { useState, useRef, useEffect, useCallback } from 'react';
import { imageAnalyzerApi } from '../../services/api/imageAnalyzerApi';

export function useImageAnalysis() {
  const [result, setResult] = useState(null);
  const [previewUrl, setPreviewUrl] = useState(null);
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

  const analyzeImage = useCallback(async (file) => {
    if (!file) {
      setError('No file provided');
      return;
    }

    abortControllerRef.current?.abort();
    abortControllerRef.current = new AbortController();
    const { signal } = abortControllerRef.current;

    try {
      setIsLoading(true);
      setError(null);
      setUploadProgress(0);
      setPreviewUrl(URL.createObjectURL(file));

      progressIntervalRef.current = setInterval(() => {
        setUploadProgress(prev => {
          if (prev >= 90) {
            clearInterval(progressIntervalRef.current);
            return prev;
          }
          return prev + 10;
        });
      }, 200);

      const analysisResult = await imageAnalyzerApi.analyzeImage(file);

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
      setError(err.response?.data?.detail || err.message || 'Failed to analyze image');
      setUploadProgress(0);
      setIsLoading(false);
    }
  }, []);

  const reset = useCallback(() => {
    abortControllerRef.current?.abort();
    setResult(null);
    setPreviewUrl(null);
    setError(null);
    setUploadProgress(0);
    setIsLoading(false);
  }, []);

  return {
    result,
    previewUrl,
    isLoading,
    error,
    uploadProgress,
    analyzeImage,
    reset
  };
}
