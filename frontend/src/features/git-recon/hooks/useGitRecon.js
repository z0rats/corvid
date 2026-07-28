import { useCallback } from 'react';
import { useAtom } from 'jotai';
import { gitReconApi } from '../services/api/gitReconApi';
import { gitReconStateAtom, GIT_RECON_INITIAL_STATE } from '../state/gitReconAtoms';
import { useResumableScan } from '../../../core/hooks/useResumableScan';
import { createLogger } from '../../../core/utils/logger';

const logger = createLogger('GitRecon');

const TERMINAL_STATUSES = ['completed', 'failed'];

// No `cancelScan` - git_recon has no cancel capability server-side, unlike
// username-search/email-search (no endpoint, no service function; a scan runs
// to completion or to its wall-clock timeout).
const api = {
  startScan: (payload, { signal }) => gitReconApi.startScan(payload, { signal }),
  fetchPersisted: (searchId) => gitReconApi.getHistory(searchId),
};

async function reduce(prev, event) {
  if (event.type === 'started') {
    return { ...prev, searchId: event.search_id };
  }
  if (event.type === 'completed') {
    const result = await gitReconApi.getHistory(event.search_id).catch((err) => {
      logger.error('Failed to fetch persisted search result:', err);
      return null;
    });
    return { ...prev, loading: false, result, error: null };
  }
  if (event.type === 'failed') {
    return { ...prev, loading: false, error: event.error };
  }
  return prev;
}

function reconcile(prev, search) {
  return {
    ...prev,
    loading: false,
    result: search.status === 'completed' ? search : prev.result,
    error: search.status === 'failed' ? (search.error || 'Scan failed') : null,
  };
}

export function useGitRecon() {
  const [state, setState] = useAtom(gitReconStateAtom);

  const { startScan: resumableStartScan } = useResumableScan({
    scopeKey: 'git-recon',
    state,
    setState,
    initialState: GIT_RECON_INITIAL_STATE,
    terminalStatuses: TERMINAL_STATUSES,
    api,
    reduce,
    reconcile,
  });

  const scan = useCallback((payload) => resumableStartScan(
    payload,
    { ...GIT_RECON_INITIAL_STATE, loading: true },
  ), [resumableStartScan]);

  return { ...state, scan };
}
