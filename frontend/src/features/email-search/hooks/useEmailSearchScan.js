import { useCallback } from 'react';
import { useAtom } from 'jotai';
import { emailScanStateAtom, SCAN_INITIAL_STATE } from '../state/scanAtoms';
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
      currentProvider: data.checker_name,
      foundProviders: data.found
        ? [...prev.foundProviders, { provider_name: data.provider_name, emails: data.emails, extra: data.extra }]
        : prev.foundProviders,
      errorCount: data.status === 'error' ? prev.errorCount + 1 : prev.errorCount,
    };
  }
  if (event.type === 'completed' || event.type === 'cancelled') {
    return {
      ...prev,
      phase: event.type,
      checked: data.total_providers_checked,
      totalProviders: data.total_providers_checked,
      searchId: data.search_id,
      errorCount: data.error_count ?? prev.errorCount,
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
    source: run.source ?? prev.source,
    username: run.username ?? prev.username,
    checked: run.total_providers_checked,
    totalProviders: run.total_providers_checked,
    foundProviders: run.provider_results || [],
    errorCount: run.error_count ?? prev.errorCount,
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
    endpoint: { base: '/api/email-search', runs: 'runs' },
    reduce,
    reconcile,
  });

  const startScan = useCallback((username, source = 'mailcat') => resumableStartScan(
    { username, source },
    buildRunningSeed(SCAN_INITIAL_STATE, { username, source }),
  ), [resumableStartScan]);

  return { ...state, startScan, cancelScan, reset };
}
