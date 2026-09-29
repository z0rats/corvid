import { atom } from 'jotai';

export const INSTAGRAM_SEARCH_INITIAL_STATE = {
  result: null,
  loading: false,
  error: null,
};

// Module-scoped atom (rather than component-local useState) so an in-flight
// lookup and its result stay visible across route changes - switching to
// another feature tab and back must not lose an in-progress or just-finished lookup.
export const instagramSearchStateAtom = atom(INSTAGRAM_SEARCH_INITIAL_STATE);
instagramSearchStateAtom.debugLabel = 'instagramSearchStateAtom';
