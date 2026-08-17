import { atom } from 'jotai';

export const RU_BUSINESS_CHECK_INITIAL_STATE = {
  result: null,
  loading: false,
  error: null,
  searchId: null,
};

// Module-scoped atom (rather than component-local useState) so an in-flight scan and its
// result stay visible across route changes - switching to another feature tab and back
// must not lose an in-progress or just-finished scan. Same pattern as git-recon.
export const ruBusinessCheckStateAtom = atom(RU_BUSINESS_CHECK_INITIAL_STATE);
ruBusinessCheckStateAtom.debugLabel = 'ruBusinessCheckStateAtom';
