import { atom } from 'jotai';

export const SCAN_INITIAL_STATE = {
  phase: 'idle', // idle | running | completed | cancelled | failed
  target: '',
  stage: '',
  sampled: 0,
  sampleTarget: 0,
  title: '',
  searchId: null,
  result: null,
  error: '',
};

// Module-scoped atom so a running scan and its result survive switching feature tabs.
export const telegramScanStateAtom = atom(SCAN_INITIAL_STATE);
telegramScanStateAtom.debugLabel = 'telegramScanStateAtom';
