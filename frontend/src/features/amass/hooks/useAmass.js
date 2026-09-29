import { useCallback } from 'react';
import { useAtom } from 'jotai';
import { amassApi } from '../services/api/amassApi';
import { amassStateAtom, AMASS_INITIAL_STATE } from '../state/amassAtoms';
import { useResumableScan } from '../../../core/hooks/useResumableScan';
import { createLogger } from '../../../core/utils/logger';

const logger = createLogger('Amass');
const TERMINAL_STATUSES = ['completed', 'cancelled', 'failed'];

const api = {
  startScan: (payload, { signal }) => amassApi.startScan(payload, { signal }),
  fetchPersisted: (searchId) => amassApi.getHistory(searchId),
  cancelScan: (searchId) => amassApi.cancelScan(searchId),
};

async function reduce(prev, event) {
  const { data } = event;
  if (event.type === 'started') {
    return { ...prev, searchId: data.search_id };
  }
  if (event.type === 'completed' || event.type === 'cancelled') {
    const result = await amassApi.getHistory(data.search_id).catch((err) => {
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

export function useAmass() {
  const [state, setState] = useAtom(amassStateAtom);
  const { startScan: resumableStartScan, cancelScan } = useResumableScan({
    scopeKey: 'amass',
    state, setState, initialState: AMASS_INITIAL_STATE,
    terminalStatuses: TERMINAL_STATUSES,
    api, reduce, reconcile,
  });
  const scan = useCallback((payload) => resumableStartScan(
    payload, { ...AMASS_INITIAL_STATE, loading: true },
  ), [resumableStartScan]);
  return { ...state, scan, cancelScan };
}
