import { atom } from 'jotai';

export const REPORT_ANALYSIS_INITIAL_STATE = {
  step: 0,
  isLoading: false,
  error: null,
  infoMessage: null,
  ranking: [],
  analysisResults: [],
};

// Module-scoped atom (rather than component-local useState) so an in-progress
// AI report keeps streaming and its results stay visible across route changes -
// switching to another feature tab and back must not lose an in-progress run.
export const reportAnalysisStateAtom = atom(REPORT_ANALYSIS_INITIAL_STATE);
reportAnalysisStateAtom.debugLabel = 'reportAnalysisStateAtom';
