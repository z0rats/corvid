import { atom } from 'jotai';
import { atomFamily } from 'jotai/utils';

export const buildInitialState = (source) => ({
  phase: 'idle', // idle | running | completed | cancelled | failed
  source, // maigret | social_analyzer | threat_actor_usernames | site_check (maigret on named sites)
  username: '',
  siteNames: [], // site_check only: the sites being checked
  siteStatuses: {}, // site_check only: site -> claimed | available | unknown | illegal, as reported
  checked: 0,
  totalSites: 0,
  currentSite: '',
  foundSites: [],
  pivots: null, // backend-computed leads for the finished run (see utils/discoveredIdentifiers)
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
