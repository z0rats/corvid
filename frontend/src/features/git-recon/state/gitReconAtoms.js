import { atom } from 'jotai';

export const GIT_RECON_INITIAL_STATE = {
  result: null,
  loading: false,
  error: null,
  searchId: null,
};

// Module-scoped atom (rather than component-local useState) so an in-flight
// scan (which can run for a while - full non-shallow clones) and its result
// stay visible across route changes - switching to another feature tab and
// back must not lose an in-progress or just-finished scan.
export const gitReconStateAtom = atom(GIT_RECON_INITIAL_STATE);
gitReconStateAtom.debugLabel = 'gitReconStateAtom';
