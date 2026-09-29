import { useCallback } from 'react';
import { useAtom } from 'jotai';
import { openSseStream, readSseEvents } from '../../../../core/services/sseStream';
import { createLogger } from '../../../../core/utils/logger';
import { reportAnalysisStateAtom, REPORT_ANALYSIS_INITIAL_STATE } from '../../state/reportAnalysisAtoms';

const logger = createLogger('ReportAnalysis');

const STREAM_PATH = '/api/newsfeed/analysis/top-articles/stream';
const STREAM_ERROR = 'An error occurred while streaming data.';

// Module-scoped, not a ref: the report must keep streaming and updating
// reportAnalysisStateAtom even after the component that started it unmounts
// (e.g. the user switches to another feature tab and back).
let activeController = null;

/** One streamed event (`ranking` -> `analysis`* -> `complete`) applied to state. */
export function applyEvent(prev, event) {
  switch (event?.type) {
    case 'ranking':
      return { ...prev, step: 3, ranking: event.articles || [], infoMessage: event.info || prev.infoMessage };
    case 'analysis':
      return event.article_result
        ? { ...prev, step: 4, analysisResults: [...prev.analysisResults, event.article_result] }
        : { ...prev, step: 4 };
    case 'complete':
      return { ...prev, step: 5, isLoading: false, infoMessage: event.message };
    default:
      return prev;
  }
}

export function useReportAnalysis() {
  const [state, setState] = useAtom(reportAnalysisStateAtom);
  const { step, isLoading, error, infoMessage, ranking, analysisResults } = state;

  const showStopButton = step >= 1 && step < 5;

  const startAnalysis = useCallback(async () => {
    activeController?.abort();
    const controller = new AbortController();
    activeController = controller;
    const { signal } = controller;

    setState({ ...REPORT_ANALYSIS_INITIAL_STATE, step: 1, isLoading: true });

    let completed = false;
    try {
      const stream = await openSseStream(STREAM_PATH, { method: 'GET', signal });
      for await (const event of readSseEvents(stream, signal)) {
        setState((prev) => applyEvent(prev, event));
        if (event?.type === 'complete') {
          completed = true;
          break;
        }
      }
      if (!completed && !signal.aborted) {
        throw new Error('stream ended before the analysis completed');
      }
    } catch (err) {
      if (signal.aborted) return;
      logger.error('Report analysis stream failed:', err);
      setState((prev) => ({ ...prev, error: STREAM_ERROR, isLoading: false, step: 0 }));
    } finally {
      if (activeController === controller) {
        controller.abort(); // closes the connection once the stream is done with
        activeController = null;
      }
    }
  }, [setState]);

  const stopAnalysis = useCallback(() => {
    if (activeController) {
      activeController.abort();
      activeController = null;
    }
    setState((prev) => ({ ...prev, step: 0, isLoading: false, infoMessage: 'Analysis stream stopped by user.' }));
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
