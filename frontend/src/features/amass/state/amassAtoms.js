import { atom } from 'jotai';

export const AMASS_INITIAL_STATE = {
  result: null, loading: false, error: null, searchId: null,
};

// Module-scoped atom (rather than component-local useState) so an in-flight
// scan and its result stay visible across route changes.
export const amassStateAtom = atom(AMASS_INITIAL_STATE);
amassStateAtom.debugLabel = 'amassStateAtom';
