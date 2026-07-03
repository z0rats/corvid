import { atom } from 'jotai';

export const EMAIL_ANALYSIS_INITIAL_STATE = {
  result: null,
  isLoading: false,
  error: null,
  uploadProgress: 0,
};

// Module-scoped atom (rather than component-local useState) so an in-progress
// analysis and its result stay visible across route changes - switching to
// another feature tab and back must not lose it.
export const emailAnalysisStateAtom = atom(EMAIL_ANALYSIS_INITIAL_STATE);
emailAnalysisStateAtom.debugLabel = 'emailAnalysisStateAtom';
