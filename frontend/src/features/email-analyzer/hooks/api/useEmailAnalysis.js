import { useCallback } from 'react';
import { useAtom } from 'jotai';
import { useTranslation } from 'react-i18next';
import { emailAnalyzerApi } from '../../services/api/emailAnalyzerApi';
import { emailAnalysisStateAtom, EMAIL_ANALYSIS_INITIAL_STATE } from '../../state/emailAnalysisAtoms';

// Module-scoped, not refs: an in-flight analysis must keep running and
// updating emailAnalysisStateAtom even after the component that started it
// unmounts (e.g. the user switches to another feature tab and back).
let progressInterval = null;
let completionTimeout = null;
let activeAbortController = null;

export function useEmailAnalysis() {
  const { t } = useTranslation('emailAnalyzer');
  const [state, setState] = useAtom(emailAnalysisStateAtom);
  const { result, isLoading, error, uploadProgress } = state;

  const analyzeEmail = useCallback(async (file) => {
    if (!file) {
      setState(prev => ({ ...prev, error: t('errors.noFileProvided') }));
      return;
    }

    activeAbortController?.abort();
    activeAbortController = new AbortController();
    const { signal } = activeAbortController;

    try {
      setState({ ...EMAIL_ANALYSIS_INITIAL_STATE, isLoading: true });

      progressInterval = setInterval(() => {
        setState(prev => {
          if (prev.uploadProgress >= 90) {
            clearInterval(progressInterval);
            return prev;
          }
          return { ...prev, uploadProgress: prev.uploadProgress + 10 };
        });
      }, 200);

      const analysisResult = await emailAnalyzerApi.analyzeEmail(file);

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
        error: err.response?.data?.detail || err.message || t('errors.analysisFailed'),
        uploadProgress: 0,
        isLoading: false,
      }));
    }
  }, [t, setState]);

  const reset = useCallback(() => {
    activeAbortController?.abort();
    clearInterval(progressInterval);
    clearTimeout(completionTimeout);
    setState(EMAIL_ANALYSIS_INITIAL_STATE);
  }, [setState]);

  return {
    result,
    isLoading,
    error,
    uploadProgress,
    analyzeEmail,
    reset
  };
}
