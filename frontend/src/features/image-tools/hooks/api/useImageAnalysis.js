import { useCallback } from 'react';
import { useAtom } from 'jotai';
import { imageAnalyzerApi } from '../../services/api/imageAnalyzerApi';
import { imageAnalysisStateAtom, IMAGE_ANALYSIS_INITIAL_STATE } from '../../state/imageAnalysisAtoms';

// Module-scoped, not refs: an in-flight analysis must keep running and
// updating imageAnalysisStateAtom even after the component that started it
// unmounts (e.g. the user switches to another feature tab and back).
let progressInterval = null;
let completionTimeout = null;
let activeAbortController = null;

export function useImageAnalysis() {
  const [state, setState] = useAtom(imageAnalysisStateAtom);
  const { result, previewUrl, isLoading, error, uploadProgress } = state;

  const analyzeImage = useCallback(async (file) => {
    if (!file) {
      setState(prev => ({ ...prev, error: 'No file provided' }));
      return;
    }

    activeAbortController?.abort();
    activeAbortController = new AbortController();
    const { signal } = activeAbortController;

    try {
      setState({ ...IMAGE_ANALYSIS_INITIAL_STATE, isLoading: true, previewUrl: URL.createObjectURL(file) });

      progressInterval = setInterval(() => {
        setState(prev => {
          if (prev.uploadProgress >= 90) {
            clearInterval(progressInterval);
            return prev;
          }
          return { ...prev, uploadProgress: prev.uploadProgress + 10 };
        });
      }, 200);

      const analysisResult = await imageAnalyzerApi.analyzeImage(file);

      if (signal.aborted) return;

      clearInterval(progressInterval);
      setState(prev => ({ ...prev, uploadProgress: 100 }));

      completionTimeout = setTimeout(() => {
        if (signal.aborted) return;
        setState(prev => ({ ...prev, result: analysisResult, uploadProgress: 0, isLoading: false }));
      }, 300);

    } catch (err) {
      if (signal.aborted) return;
      clearInterval(progressInterval);
      setState(prev => ({
        ...prev,
        error: err.response?.data?.detail || err.message || 'Failed to analyze image',
        uploadProgress: 0,
        isLoading: false,
      }));
    }
  }, [setState]);

  const reset = useCallback(() => {
    activeAbortController?.abort();
    clearInterval(progressInterval);
    clearTimeout(completionTimeout);
    setState(IMAGE_ANALYSIS_INITIAL_STATE);
  }, [setState]);

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
