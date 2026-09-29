import { atom } from 'jotai';

export const STEAM_PROFILE_INITIAL_STATE = {
  result: null,
  loading: false,
  error: null,
  errorCode: null,
};

// Module-scoped atom (rather than component-local useState) so an in-flight lookup and its
// result survive switching to another feature tab and back.
export const steamProfileStateAtom = atom(STEAM_PROFILE_INITIAL_STATE);
steamProfileStateAtom.debugLabel = 'steamProfileStateAtom';

export const SCAN_INITIAL_STATE = {
  phase: 'idle', // idle | running | completed | cancelled | failed
  target: '',
  stage: '',
  friendsTotal: 0,
  analyzed: 0,
  candidatesSelected: 0,
  searchId: null,
  result: null,
  error: '',
};

// Same module-scoped-atom rationale as steamProfileStateAtom: a running scan (and its final
// result) must survive a tab switch, not just a re-render.
export const steamReconScanStateAtom = atom(SCAN_INITIAL_STATE);
steamReconScanStateAtom.debugLabel = 'steamReconScanStateAtom';
