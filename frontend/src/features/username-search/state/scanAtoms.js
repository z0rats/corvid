import { atom } from 'jotai';
import { atomFamily } from 'jotai/utils';

export const buildInitialState = (source) => ({
  phase: 'idle', // idle | running | completed | cancelled | failed
  source, // maigret | social_analyzer | threat_actor_usernames
  username: '',
  checked: 0,
  totalSites: 0,
  currentSite: '',
  foundSites: [],
  searchId: null,
  error: '',
});

// One atom per module (rather than a single shared atom) so multiple scans can run in
// parallel, each surviving route changes independently - switching to another feature
// tab and back must not lose any of them.
export const usernameScanStateAtomFamily = atomFamily((source) => {
  const scanAtom = atom(buildInitialState(source));
  scanAtom.debugLabel = `usernameScanStateAtom-${source}`;
  return scanAtom;
});
