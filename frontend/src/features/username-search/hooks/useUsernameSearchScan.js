import { useCallback } from 'react';
import { useAtom } from 'jotai';
import { usernameSearchApi } from '../services/api/usernameSearchApi';
import { usernameScanStateAtom, SCAN_INITIAL_STATE } from '../state/scanAtoms';
import { createLogger } from '../../../core/utils/logger';

const logger = createLogger('UsernameSearchScan');

// Module-scoped, not a ref: the scan must keep reading its SSE stream and
// updating usernameScanStateAtom even after the component that started it
// unmounts (e.g. the user switches to another feature tab and back).
let activeAbortController = null;

const TERMINAL_STATUSES = ['completed', 'cancelled', 'failed'];
const RECONCILE_POLL_INTERVAL_MS = 2000;
const RECONCILE_POLL_MAX_ATTEMPTS = 150; // ~5 minutes

// Sources whose "completed"/"cancelled" SSE events don't carry the found-site
// list inline (only counts) - social-analyzer has no per-site progress event to
// have accumulated it from, so it must be fetched from the persisted run instead.
async function fetchFoundSites(searchId) {
  try {
    const run = await usernameSearchApi.getRun(searchId);
    return run.site_results || [];
  } catch (err) {
    logger.error('Failed to fetch persisted site results:', err);
    return null;
  }
}

export function useUsernameSearchScan() {
  const [state, setState] = useAtom(usernameScanStateAtom);

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
            setState(prev => ({ ...prev, searchId: event.search_id, totalSites: event.total_sites }));
          } else if (event.type === 'progress') {
            setState(prev => ({
              ...prev,
              checked: event.checked,
              totalSites: event.total_sites,
              currentSite: event.site_name,
              foundSites: event.found
                ? [...prev.foundSites, { site_name: event.site_name, url_user: event.url_user }]
                : prev.foundSites,
            }));
          } else if (event.type === 'completed' || event.type === 'cancelled') {
            const foundSites = await fetchFoundSites(event.search_id);
            setState(prev => ({
              ...prev,
              phase: event.type,
              checked: event.total_sites_checked,
              totalSites: event.total_sites_checked,
              searchId: event.search_id,
              foundSites: foundSites ?? prev.foundSites,
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

  // The backend scan runs independently of this connection (see username_search_service's
  // docstring) - if the SSE stream itself drops (network hiccup, proxy timeout), the scan
  // may still be running or may have already finished server-side. Poll the persisted run
  // instead of assuming failure, so the UI doesn't show "failed" for a scan that actually
  // succeeded.
  const reconcileAfterStreamError = useCallback(async (searchId, signal) => {
    for (let attempt = 0; attempt < RECONCILE_POLL_MAX_ATTEMPTS; attempt++) {
      if (signal.aborted) return;
      let run;
      try {
        run = await usernameSearchApi.getRun(searchId);
      } catch (err) {
        logger.error('Failed to reconcile scan state after connection error:', err);
        break;
      }

      if (TERMINAL_STATUSES.includes(run.status)) {
        setState(prev => ({
          ...prev,
          phase: run.status,
          checked: run.total_sites_checked,
          totalSites: run.total_sites_checked,
          foundSites: run.site_results || [],
          error: run.error_message || '',
        }));
        return;
      }

      await new Promise(resolve => setTimeout(resolve, RECONCILE_POLL_INTERVAL_MS));
    }
    // Gave up waiting - the run may still genuinely be in progress server-side,
    // but there's no live connection left to keep watching it from here.
    setState(prev => ({ ...prev, phase: 'failed', error: 'Lost connection to the server' }));
  }, [setState]);

  const startScan = useCallback(async (username, options = {}) => {
    if (activeAbortController) {
      activeAbortController.abort();
    }
    activeAbortController = new AbortController();
    const { signal } = activeAbortController;
    const searchIdRef = { current: null };

    setState({ ...SCAN_INITIAL_STATE, phase: 'running', username, source: options.source || 'maigret' });

    try {
      const stream = await usernameSearchApi.startScan(username, { ...options, signal });
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
      usernameSearchApi.cancelScan(prev.searchId).catch(err => logger.error('Cancel request failed:', err));
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
