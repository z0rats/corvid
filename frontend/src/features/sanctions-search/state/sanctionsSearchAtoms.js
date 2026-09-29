import { atom } from 'jotai';

export const SANCTIONS_SEARCH_INITIAL_STATE = {
  result: null,
  loading: false,
  error: null,
};

// Module-scoped atom (rather than component-local useState) so an in-flight search and its
// result stay visible across route changes - switching to another feature tab and back must
// not lose an in-progress or just-finished search.
export const sanctionsSearchStateAtom = atom(SANCTIONS_SEARCH_INITIAL_STATE);
sanctionsSearchStateAtom.debugLabel = 'sanctionsSearchStateAtom';
