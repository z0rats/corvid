import { useCallback } from 'react';
import { useAtom } from 'jotai';
import { instagramSearchApi } from '../../services/api/instagramSearchApi';
import { instagramScanStateAtom, INSTAGRAM_SCAN_INITIAL_STATE } from '../../state/instagramScanAtoms';
import { useResumableScan } from '../../../../core/hooks/useResumableScan';
import { createLogger } from '../../../../core/utils/logger';

const logger = createLogger('InstagramScan');

const TERMINAL_STATUSES = ['completed', 'cancelled', 'failed'];

const api = {
  startScan: (payload, { signal }) => instagramSearchApi.startScan(payload, { signal }),
  fetchPersisted: (searchId) => instagramSearchApi.getHistory(searchId),
  cancelScan: (searchId) => instagramSearchApi.cancelScan(searchId),
};

async function reduce(prev, event) {
  const { data } = event;
  if (event.type === 'started') {
    return { ...prev, searchId: data.search_id };
  }
  if (event.type === 'completed' || event.type === 'cancelled') {
    const result = await instagramSearchApi.getHistory(data.search_id).catch((err) => {
      logger.error('Failed to fetch persisted scan result:', err);
      return null;
    });
    return { ...prev, loading: false, result, error: null };
  }
  if (event.type === 'failed') {
    return { ...prev, loading: false, error: data.error };
  }
  return prev;
}

function reconcile(prev, search) {
  return {
    ...prev,
    loading: false,
    result: search.status === 'completed' || search.status === 'cancelled' ? search : prev.result,
    error: search.status === 'failed' ? (search.error || 'Scan failed') : null,
  };
}

export function useInstagramScan() {
  const [state, setState] = useAtom(instagramScanStateAtom);

  const { startScan: resumableStartScan, cancelScan } = useResumableScan({
    scopeKey: 'instagram-search-scan',
    state,
    setState,
    initialState: INSTAGRAM_SCAN_INITIAL_STATE,
    terminalStatuses: TERMINAL_STATUSES,
    api,
    reduce,
    reconcile,
  });

  const scan = useCallback((payload) => resumableStartScan(
    payload,
    { ...INSTAGRAM_SCAN_INITIAL_STATE, loading: true },
  ), [resumableStartScan]);

  return { ...state, scan, cancelScan };
}
