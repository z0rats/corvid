import { useCallback } from 'react';
import { useAtom } from 'jotai';
import { phoneScanStateAtom, SCAN_INITIAL_STATE } from '../state/scanAtoms';
import { useResumableScan, failedReduce, buildRunningSeed } from '../../../core/hooks/useResumableScan';

export function reduce(prev, event) {
  const { data } = event;
  if (event.type === 'started') {
    return { ...prev, searchId: data.search_id, totalProviders: data.total_providers };
  }
  if (event.type === 'progress') {
    return {
      ...prev,
      checked: data.checked,
      totalProviders: data.total_providers,
      currentProvider: data.provider_name,
      foundProviders: data.found
        ? [...prev.foundProviders, { provider_name: data.provider_name }]
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

export function reconcile(prev, run) {
  return {
    ...prev,
    phase: run.status,
    checked: run.total_providers_checked,
    totalProviders: run.total_providers_checked,
    foundProviders: run.provider_results || [],
    error: run.error_message || '',
  };
}

export function usePhoneSearchScan() {
  const [state, setState] = useAtom(phoneScanStateAtom);

  const { startScan: resumableStartScan, cancelScan, reset } = useResumableScan({
    scopeKey: 'phone-search',
    state,
    setState,
    initialState: SCAN_INITIAL_STATE,
    endpoint: { base: '/api/phone-search', runs: 'runs' },
    reduce,
    reconcile,
  });

  const startScan = useCallback((phoneNumber) => resumableStartScan(
    { phone_number: phoneNumber },
    buildRunningSeed(SCAN_INITIAL_STATE, { phoneNumber }),
  ), [resumableStartScan]);

  return { ...state, startScan, cancelScan, reset };
}
