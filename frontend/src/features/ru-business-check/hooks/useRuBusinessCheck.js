import { useCallback } from 'react';
import { useAtom } from 'jotai';
import { ruBusinessCheckApi } from '../services/api/ruBusinessCheckApi';
import { RU_BUSINESS_CHECK_INITIAL_STATE, ruBusinessCheckStateAtom } from '../state/ruBusinessCheckAtoms';
import { useResumableScan } from '../../../core/hooks/useResumableScan';
import { createLogger } from '../../../core/utils/logger';

const logger = createLogger('RuBusinessCheck');

const TERMINAL_STATUSES = ['completed', 'cancelled', 'failed'];

const api = {
  startScan: (payload, { signal }) => ruBusinessCheckApi.startScan(payload, { signal }),
  fetchPersisted: (searchId) => ruBusinessCheckApi.getHistory(searchId),
  cancelScan: (searchId) => ruBusinessCheckApi.cancelScan(searchId),
};

async function reduce(prev, event) {
  const { data } = event;
  if (event.type === 'started') {
    return { ...prev, searchId: data.search_id };
  }
  if (event.type === 'completed' || event.type === 'cancelled') {
    const result = await ruBusinessCheckApi.getHistory(data.search_id).catch((err) => {
      logger.error('Failed to fetch persisted search result:', err);
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
    error: search.status === 'failed' ? (search.error || 'Проверка завершилась с ошибкой') : null,
  };
}

export function useRuBusinessCheck() {
  const [state, setState] = useAtom(ruBusinessCheckStateAtom);

  const { startScan: resumableStartScan, cancelScan } = useResumableScan({
    scopeKey: 'ru-business-check',
    state,
    setState,
    initialState: RU_BUSINESS_CHECK_INITIAL_STATE,
    terminalStatuses: TERMINAL_STATUSES,
    api,
    reduce,
    reconcile,
  });

  const scan = useCallback((payload) => resumableStartScan(
    payload,
    { ...RU_BUSINESS_CHECK_INITIAL_STATE, loading: true },
  ), [resumableStartScan]);

  return { ...state, scan, cancelScan };
}
