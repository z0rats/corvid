import { useCallback } from 'react';
import { useAtom } from 'jotai';
import { emailSearchApi } from '../services/api/emailSearchApi';
import { emailScanStateAtom, SCAN_INITIAL_STATE } from '../state/scanAtoms';
import { createLogger } from '../../../core/utils/logger';

const logger = createLogger('EmailSearchScan');

const sleep = (ms) => new Promise(resolve => setTimeout(resolve, ms));

// Module-scoped, not a ref: the scan must keep reading its SSE stream and
// updating emailScanStateAtom even after the component that started it
// unmounts (e.g. the user switches to another feature tab and back).
let activeAbortController = null;

const TERMINAL_STATUSES = ['completed', 'cancelled', 'failed'];
const RECONCILE_POLL_INITIAL_MS = 1000;
const RECONCILE_POLL_MAX_MS = 15000;
const RECONCILE_POLL_BACKOFF_FACTOR = 1.5;
const RECONCILE_POLL_TIMEOUT_MS = 5 * 60 * 1000; // give up waiting after ~5 minutes total

export function useEmailSearchScan() {
  const [state, setState] = useAtom(emailScanStateAtom);

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
            setState(prev => ({ ...prev, searchId: event.search_id, totalProviders: event.total_providers }));
          } else if (event.type === 'progress') {
            setState(prev => ({
              ...prev,
              checked: event.checked,
              totalProviders: event.total_providers,
              currentProvider: event.checker_name,
              foundProviders: event.found
                ? [...prev.foundProviders, { provider_name: event.provider_name, emails: event.emails }]
                : prev.foundProviders,
            }));
          } else if (event.type === 'completed' || event.type === 'cancelled') {
            setState(prev => ({
              ...prev,
              phase: event.type,
              checked: event.total_providers_checked,
              totalProviders: event.total_providers_checked,
              searchId: event.search_id,
            }));
          } else if (event.type === 'failed') {
            setState(prev => ({ ...prev, phase: 'failed', error: event.error, searchId: event.search_id }));
          }
        }
      }
    } finally {
      reader.releaseLock();
    }
  }, [setState]);

  // The backend scan runs independently of this connection (see email_search_service's
  // docstring) - if the SSE stream itself drops (network hiccup, proxy timeout), the scan
  // may still be running or may have already finished server-side. Poll the persisted run
  // instead of assuming failure, so the UI doesn't show "failed" for a scan that actually
  // succeeded.
  const reconcileAfterStreamError = useCallback(async (searchId, signal) => {
    const startedAt = Date.now();
    let delay = RECONCILE_POLL_INITIAL_MS;

    while (Date.now() - startedAt < RECONCILE_POLL_TIMEOUT_MS) {
      if (signal.aborted) return;
      let run;
      try {
        run = await emailSearchApi.getRun(searchId);
      } catch (err) {
        logger.error('Failed to reconcile scan state after connection error:', err);
        break;
      }

      if (TERMINAL_STATUSES.includes(run.status)) {
        setState(prev => ({
          ...prev,
          phase: run.status,
          checked: run.total_providers_checked,
          totalProviders: run.total_providers_checked,
          foundProviders: run.provider_results || [],
          error: run.error_message || '',
        }));
        return;
      }

      await sleep(delay);
      delay = Math.min(delay * RECONCILE_POLL_BACKOFF_FACTOR, RECONCILE_POLL_MAX_MS);
    }
    // Gave up waiting - the run may still genuinely be in progress server-side,
    // but there's no live connection left to keep watching it from here.
    setState(prev => ({ ...prev, phase: 'failed', error: 'Lost connection to the server' }));
  }, [setState]);

  const startScan = useCallback(async (username) => {
    if (activeAbortController) {
      activeAbortController.abort();
    }
    activeAbortController = new AbortController();
    const { signal } = activeAbortController;
    const searchIdRef = { current: null };

    setState({ ...SCAN_INITIAL_STATE, phase: 'running', username });

    try {
      const stream = await emailSearchApi.startScan(username, { signal });
      await processStream(stream, signal, searchIdRef);
    } catch (err) {
      if (signal.aborted) return;
      logger.error('Scan connection error:', err);
      if (searchIdRef.current != null) {
        await reconcileAfterStreamError(searchIdRef.current, signal);
      } else {
        setState(prev => ({ ...prev, phase: 'failed', error: err.message }));
      }
    }
  }, [processStream, reconcileAfterStreamError, setState]);

  const cancelScan = useCallback(async () => {
    setState(prev => {
      if (prev.searchId == null || prev.phase !== 'running') return prev;
      emailSearchApi.cancelScan(prev.searchId).catch(err => logger.error('Cancel request failed:', err));
      return prev;
    });
  }, [setState]);

  const reset = useCallback(() => {
    if (activeAbortController) {
      activeAbortController.abort();
      activeAbortController = null;
    }
    setState(SCAN_INITIAL_STATE);
  }, [setState]);

  return { ...state, startScan, cancelScan, reset };
}
