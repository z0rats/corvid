import { atom } from 'jotai';

export const INSTAGRAM_SCAN_INITIAL_STATE = {
  result: null,
  loading: false,
  error: null,
  searchId: null,
};

// Module-scoped atom (rather than component-local useState) so an in-flight
// scan and its result stay visible across route changes - switching to
// another feature tab and back must not lose an in-progress or just-finished scan.
export const instagramScanStateAtom = atom(INSTAGRAM_SCAN_INITIAL_STATE);
instagramScanStateAtom.debugLabel = 'instagramScanStateAtom';
