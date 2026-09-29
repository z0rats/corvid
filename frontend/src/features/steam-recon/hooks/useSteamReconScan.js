import { useCallback } from 'react';
import { useAtom } from 'jotai';
import { steamReconApi } from '../services/api/steamReconApi';
import { steamReconScanStateAtom, SCAN_INITIAL_STATE } from '../state/steamReconAtoms';
import { useResumableScan, failedReduce, buildRunningSeed } from '../../../core/hooks/useResumableScan';
import { createLogger } from '../../../core/utils/logger';

const logger = createLogger('SteamReconScan');
const TERMINAL_STATUSES = ['completed', 'cancelled', 'failed'];

const api = {
  startScan: (payload, { signal }) => steamReconApi.startScan(payload, { signal }),
  fetchPersisted: (searchId) => steamReconApi.getSearch(searchId),
  cancelScan: (searchId) => steamReconApi.cancelScan(searchId),
};

// `completed`/`cancelled` events only carry scalar summary fields (see ScanOutcome's
// `db_only_fields` - the full result blob is never echoed on the wire), so this fetches the
// persisted record for its `result` the same way git_recon's reduce does.
export async function reduce(prev, event) {
  const { data } = event;
  if (event.type === 'started') {
    return { ...prev, searchId: data.search_id };
  }
  if (event.type === 'progress') {
    return {
      ...prev,
      stage: data.stage,
      friendsTotal: data.friends_total ?? prev.friendsTotal,
      candidatesSelected: data.candidates_selected ?? prev.candidatesSelected,
      analyzed: data.analyzed ?? prev.analyzed,
    };
  }
  if (event.type === 'completed' || event.type === 'cancelled') {
    const result = await steamReconApi.getSearch(data.search_id).catch((err) => {
      logger.error('Failed to fetch persisted scan result:', err);
      return null;
    });
    return { ...prev, phase: event.type, searchId: data.search_id, result };
  }
  if (event.type === 'failed') {
    return failedReduce(prev, event);
  }
  return prev;
}

export function reconcile(prev, search) {
  return {
    ...prev,
    phase: search.status,
    result: search.status === 'completed' || search.status === 'cancelled' ? search : prev.result,
    error: search.status === 'failed' ? search.error_message || 'Scan failed' : '',
  };
}

export function useSteamReconScan() {
  const [state, setState] = useAtom(steamReconScanStateAtom);

  const { startScan: resumableStartScan, cancelScan } = useResumableScan({
    scopeKey: 'steam-recon',
    state,
    setState,
    initialState: SCAN_INITIAL_STATE,
    terminalStatuses: TERMINAL_STATUSES,
    api,
    reduce,
    reconcile,
  });

  const startScan = useCallback(
    (target, { maxFriends, includeCsReport }) =>
      resumableStartScan(
        { target, maxFriends, includeCsReport },
        buildRunningSeed(SCAN_INITIAL_STATE, { target }),
      ),
    [resumableStartScan],
  );

  return { ...state, startScan, cancelScan };
}
