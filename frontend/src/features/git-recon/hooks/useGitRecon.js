import { useCallback } from 'react';
import { useAtom } from 'jotai';
import { gitReconApi } from '../services/api/gitReconApi';
import { gitReconStateAtom, GIT_RECON_INITIAL_STATE } from '../state/gitReconAtoms';
import { createLogger } from '../../../core/utils/logger';

const logger = createLogger('GitRecon');

const sleep = (ms) => new Promise(resolve => setTimeout(resolve, ms));

// Module-scoped, not a ref: the scan must keep reading its SSE stream even
// after the component that started it unmounts (e.g. the user switches to
// another feature tab and back).
let activeAbortController = null;

const TERMINAL_STATUSES = ['completed', 'failed'];
const RECONCILE_POLL_INITIAL_MS = 1000;
const RECONCILE_POLL_MAX_MS = 15000;
const RECONCILE_POLL_BACKOFF_FACTOR = 1.5;
const RECONCILE_POLL_TIMEOUT_MS = 5 * 60 * 1000; // give up waiting after ~5 minutes total

export function useGitRecon() {
  const [state, setState] = useAtom(gitReconStateAtom);

  const processStream = useCallback(async (stream, signal, searchIdRef) => {
    const reader = stream.getReader();
    const decoder = new TextDecoder();
    let buffer = '';

    try {
      while (true) {
        if (signal?.aborted) break;
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const chunks = buffer.split('\n\n');
        buffer = chunks.pop();

        for (const chunk of chunks) {
          if (!chunk.startsWith('data: ')) continue;

          let event;
          try {
            event = JSON.parse(chunk.substring(6));
          } catch (err) {
            logger.error('Failed to parse SSE event:', err, chunk);
            continue;
          }

          if (event.type === 'started') {
            if (searchIdRef) searchIdRef.current = event.search_id;
            setState(prev => ({ ...prev, searchId: event.search_id }));
          } else if (event.type === 'completed') {
            const result = await gitReconApi.getHistory(event.search_id).catch(err => {
              logger.error('Failed to fetch persisted search result:', err);
              return null;
            });
            setState(prev => ({ ...prev, loading: false, result, error: null }));
          } else if (event.type === 'failed') {
            setState(prev => ({ ...prev, loading: false, error: event.error }));
          }
        }
      }
    } finally {
      reader.releaseLock();
    }
  }, [setState]);

  // The backend scan runs independently of this connection (see git_recon_service's
  // run_scan_task docstring) - if the SSE stream itself drops (network hiccup, proxy
  // timeout), the scan may still be running or may have already finished server-side.
  // Poll the persisted search instead of assuming failure, so the UI doesn't show
  // "failed" for a scan that actually succeeded.
  const reconcileAfterStreamError = useCallback(async (searchId, signal) => {
    const startedAt = Date.now();
    let delay = RECONCILE_POLL_INITIAL_MS;

    while (Date.now() - startedAt < RECONCILE_POLL_TIMEOUT_MS) {
      if (signal.aborted) return;
      let search;
      try {
        search = await gitReconApi.getHistory(searchId);
      } catch (err) {
        logger.error('Failed to reconcile scan state after connection error:', err);
        break;
      }

      if (TERMINAL_STATUSES.includes(search.status)) {
        setState(prev => ({
          ...prev,
          loading: false,
          result: search.status === 'completed' ? search : prev.result,
          error: search.status === 'failed' ? (search.error || 'Scan failed') : null,
        }));
        return;
      }

      await sleep(delay);
      delay = Math.min(delay * RECONCILE_POLL_BACKOFF_FACTOR, RECONCILE_POLL_MAX_MS);
    }
    // Gave up waiting - the scan may still genuinely be in progress server-side,
    // but there's no live connection left to keep watching it from here.
    setState(prev => ({ ...prev, loading: false, error: 'Lost connection to the server' }));
  }, [setState]);

  const scan = useCallback(async (payload) => {
    if (activeAbortController) {
      activeAbortController.abort();
    }
    activeAbortController = new AbortController();
    const { signal } = activeAbortController;
    const searchIdRef = { current: null };

    setState({ ...GIT_RECON_INITIAL_STATE, loading: true });

    try {
      const stream = await gitReconApi.startScan(payload, { signal });
      await processStream(stream, signal, searchIdRef);
    } catch (err) {
      if (signal.aborted) return;
      logger.error('Scan connection error:', err);
      if (searchIdRef.current != null) {
        await reconcileAfterStreamError(searchIdRef.current, signal);
      } else {
        setState(prev => ({ ...prev, loading: false, error: err.message }));
      }
    }
  }, [processStream, reconcileAfterStreamError, setState]);

  return { ...state, scan };
}
