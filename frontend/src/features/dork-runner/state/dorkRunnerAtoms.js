import { atom } from 'jotai';

export const DORK_RUNNER_INITIAL_STATE = {
  result: null,
  loading: false,
  error: null,
};

// Module-scoped atom (rather than component-local useState) so an in-flight
// dork run and its result stay visible across route changes - switching to
// another feature tab and back must not lose an in-progress or just-finished run.
export const dorkRunnerStateAtom = atom(DORK_RUNNER_INITIAL_STATE);
dorkRunnerStateAtom.debugLabel = 'dorkRunnerStateAtom';
