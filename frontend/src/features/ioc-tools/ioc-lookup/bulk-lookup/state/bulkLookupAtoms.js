import { atom } from 'jotai';
import { IOC_TYPES } from '../../shared/utils/iocDefinitions';

export const BULK_LOOKUP_INITIAL_STATE = {
  categorizedIocs: Object.fromEntries(Object.values(IOC_TYPES).map(type => [type, []])),
  loading: false,
  progress: 0,
  processorError: '',
};

// Module-scoped atom (rather than component-local useState) so an in-progress
// bulk lookup keeps streaming and its results stay visible across route changes -
// switching to another feature tab and back must not lose an in-progress run.
export const bulkLookupStateAtom = atom(BULK_LOOKUP_INITIAL_STATE);
bulkLookupStateAtom.debugLabel = 'bulkLookupStateAtom';
