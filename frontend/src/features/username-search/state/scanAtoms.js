import { atom } from 'jotai';

export const SCAN_INITIAL_STATE = {
  phase: 'idle', // idle | running | completed | cancelled | failed
  source: 'maigret', // maigret | social_analyzer
  username: '',
  checked: 0,
  totalSites: 0,
  currentSite: '',
  foundSites: [],
  searchId: null,
  error: '',
};

// Module-scoped atom (rather than component-local useState) so the live scan
// keeps streaming and its progress stays visible across route changes -
// switching to another feature tab and back must not lose an in-progress search.
export const usernameScanStateAtom = atom(SCAN_INITIAL_STATE);
usernameScanStateAtom.debugLabel = 'usernameScanStateAtom';
