import { atom } from 'jotai';

export const SCAN_INITIAL_STATE = {
  phase: 'idle', // idle | running | completed | cancelled | failed
  username: '',
  checked: 0,
  totalProviders: 0,
  currentProvider: '',
  foundProviders: [],
  searchId: null,
  error: '',
};

// Module-scoped atom (rather than component-local useState) so the live scan
// keeps streaming and its progress stays visible across route changes -
// switching to another feature tab and back must not lose an in-progress search.
export const emailScanStateAtom = atom(SCAN_INITIAL_STATE);
emailScanStateAtom.debugLabel = 'emailScanStateAtom';
