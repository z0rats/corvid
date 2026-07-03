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

export function useUsernameSearchScan() {
  const [state, setState] = useAtom(usernameScanStateAtom);

  const processStream = useCallback(async (stream, signal) => {
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
          } else if (event.type === 'completed') {
            setState(prev => ({
              ...prev,
              phase: 'completed',
              checked: event.total_sites_checked,
              totalSites: event.total_sites_checked,
              searchId: event.search_id,
            }));
          } else if (event.type === 'cancelled') {
            setState(prev => ({
              ...prev,
              phase: 'cancelled',
              checked: event.total_sites_checked,
              totalSites: event.total_sites_checked,
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

  const startScan = useCallback(async (username, options = {}) => {
    if (activeAbortController) {
      activeAbortController.abort();
    }
    activeAbortController = new AbortController();
    const { signal } = activeAbortController;

    setState({ ...SCAN_INITIAL_STATE, phase: 'running', username });

    try {
      const stream = await usernameSearchApi.startScan(username, { ...options, signal });
      await processStream(stream, signal);
    } catch (err) {
      if (signal.aborted) return;
      logger.error('Scan connection error:', err);
      setState(prev => ({ ...prev, phase: 'failed', error: err.message }));
    }
  }, [processStream, setState]);

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
