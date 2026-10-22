import { useCallback } from 'react';
import { useAtom } from 'jotai';
import { telegramSearchApi } from '../services/api/telegramSearchApi';
import { telegramScanStateAtom, SCAN_INITIAL_STATE } from '../state/telegramScanAtoms';
import { useResumableScan, failedReduce, buildRunningSeed } from '../../../core/hooks/useResumableScan';
import { createLogger } from '../../../core/utils/logger';

const logger = createLogger('TelegramScan');

// `completed`/`cancelled` carry only the summary columns (the result blob is never echoed on the
// wire), so the persisted record is fetched for it.
export async function reduce(prev, event) {
  const { data } = event;
  if (event.type === 'started') {
    return { ...prev, searchId: data.search_id };
  }
  if (event.type === 'progress') {
    return {
      ...prev,
      stage: data.stage,
      title: data.title ?? prev.title,
      sampled: data.sampled ?? prev.sampled,
      sampleTarget: data.target ?? prev.sampleTarget,
    };
  }
  if (event.type === 'completed' || event.type === 'cancelled') {
    const result = await telegramSearchApi.getSearch(data.search_id).catch((err) => {
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

export function useTelegramScan() {
  const [state, setState] = useAtom(telegramScanStateAtom);

  const { startScan: resumableStartScan, cancelScan } = useResumableScan({
    scopeKey: 'telegram-search',
    state,
    setState,
    initialState: SCAN_INITIAL_STATE,
    endpoint: { base: '/api/telegram-search', runs: 'history' },
    reduce,
    reconcile,
  });

  const startScan = useCallback(
    (target, { maxPosts }) =>
      resumableStartScan(
        { target, max_posts: maxPosts },
        buildRunningSeed(SCAN_INITIAL_STATE, { target }),
      ),
    [resumableStartScan],
  );

  return { ...state, startScan, cancelScan };
}
