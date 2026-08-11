import { useCallback } from 'react';
import { useAtom } from 'jotai';
import { emailSearchApi } from '../services/api/emailSearchApi';
import { emailScanStateAtom, SCAN_INITIAL_STATE } from '../state/scanAtoms';
import { useResumableScan, failedReduce, buildRunningSeed } from '../../../core/hooks/useResumableScan';

const TERMINAL_STATUSES = ['completed', 'cancelled', 'failed'];

const api = {
  startScan: (payload, { signal }) => emailSearchApi.startScan(payload.username, { signal }),
  fetchPersisted: (searchId) => emailSearchApi.getRun(searchId),
  cancelScan: (searchId) => emailSearchApi.cancelScan(searchId),
};

function reduce(prev, event) {
  const { data } = event;
  if (event.type === 'started') {
    return { ...prev, searchId: data.search_id, totalProviders: data.total_providers };
  }
  if (event.type === 'progress') {
    return {
      ...prev,
      checked: data.checked,
      totalProviders: data.total_providers,
      currentProvider: data.checker_name,
      foundProviders: data.found
        ? [...prev.foundProviders, { provider_name: data.provider_name, emails: data.emails }]
        : prev.foundProviders,
    };
  }
  if (event.type === 'completed' || event.type === 'cancelled') {
    return {
      ...prev,
      phase: event.type,
      checked: data.total_providers_checked,
      totalProviders: data.total_providers_checked,
      searchId: data.search_id,
    };
  }
  if (event.type === 'failed') {
    return failedReduce(prev, event);
  }
  return prev;
}

function reconcile(prev, run) {
  return {
    ...prev,
    phase: run.status,
    checked: run.total_providers_checked,
    totalProviders: run.total_providers_checked,
    foundProviders: run.provider_results || [],
    error: run.error_message || '',
  };
}

export function useEmailSearchScan() {
  const [state, setState] = useAtom(emailScanStateAtom);

  const { startScan: resumableStartScan, cancelScan, reset } = useResumableScan({
    scopeKey: 'email-search',
    state,
    setState,
    initialState: SCAN_INITIAL_STATE,
    terminalStatuses: TERMINAL_STATUSES,
    api,
    reduce,
    reconcile,
  });

  const startScan = useCallback((username) => resumableStartScan(
    { username },
    buildRunningSeed(SCAN_INITIAL_STATE, { username }),
  ), [resumableStartScan]);

  return { ...state, startScan, cancelScan, reset };
}
