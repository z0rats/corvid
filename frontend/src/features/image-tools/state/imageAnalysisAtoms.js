import { atom } from 'jotai';

export const IMAGE_ANALYSIS_INITIAL_STATE = {
  result: null,
  previewUrl: null,
  isLoading: false,
  error: null,
  uploadProgress: 0,
};

// Module-scoped atom (rather than component-local useState) so an in-progress
// analysis and its result stay visible across route changes - switching to
// another feature tab and back must not lose it.
export const imageAnalysisStateAtom = atom(IMAGE_ANALYSIS_INITIAL_STATE);
imageAnalysisStateAtom.debugLabel = 'imageAnalysisStateAtom';
