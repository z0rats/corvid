import { useCallback } from 'react';
import { useAtom } from 'jotai';
import { getStreamUrl } from '../../utils/urlUtils';
import { createLogger } from '../../../../core/utils/logger';
import { reportAnalysisStateAtom, REPORT_ANALYSIS_INITIAL_STATE } from '../../state/reportAnalysisAtoms';

const logger = createLogger('ReportAnalysis');

// Module-scoped, not a ref: the report must keep streaming and updating
// reportAnalysisStateAtom even after the component that started it unmounts
// (e.g. the user switches to another feature tab and back).
let activeEventSource = null;

export function useReportAnalysis() {
  const [state, setState] = useAtom(reportAnalysisStateAtom);
  const { step, isLoading, error, infoMessage, ranking, analysisResults } = state;

  const showStopButton = step >= 1 && step < 5;

  const startAnalysis = useCallback(() => {
    if (activeEventSource) {
      activeEventSource.close();
    }

    setState({
      ...REPORT_ANALYSIS_INITIAL_STATE,
      step: 1,
      isLoading: true,
    });

    const url = getStreamUrl();
    const es = new EventSource(url);
    activeEventSource = es;

    es.onmessage = (event) => {
      const rawData = event.data;
      if (!rawData || !rawData.trim()) return;

      try {
        const parsed = JSON.parse(rawData);

        switch (parsed.type) {
          case 'ranking':
            setState(prev => ({
              ...prev,
              step: 3,
              ranking: parsed.articles || [],
              infoMessage: parsed.info || prev.infoMessage,
            }));
            break;
          case 'analysis':
            if (parsed.article_result) {
              setState(prev => ({
                ...prev,
                step: 4,
                analysisResults: [...prev.analysisResults, parsed.article_result],
              }));
            } else {
              setState(prev => ({ ...prev, step: 4 }));
            }
            break;
          case 'complete':
            setState(prev => ({ ...prev, step: 5, isLoading: false, infoMessage: parsed.message }));
            es.close();
            activeEventSource = null;
            break;
          default:
            break;
        }
      } catch (err) {
        logger.error('SSE parse error:', err);
      }
    };

    es.onerror = () => {
      setState(prev => ({ ...prev, error: 'An error occurred while streaming data.', isLoading: false, step: 0 }));
      if (activeEventSource) {
        activeEventSource.close();
        activeEventSource = null;
      }
    };
  }, [setState]);

  const stopAnalysis = useCallback(() => {
    if (activeEventSource) {
      activeEventSource.close();
      activeEventSource = null;
    }
    setState(prev => ({ ...prev, step: 0, isLoading: false, infoMessage: 'Analysis stream stopped by user.' }));
  }, [setState]);

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
