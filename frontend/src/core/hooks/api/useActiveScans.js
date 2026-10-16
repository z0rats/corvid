import { useCallback, useEffect, useRef, useState } from 'react';
import { activityService } from '../../services/api/activityService';
import { createLogger } from '../../utils/logger';
import { SCAN_LIFECYCLE_EVENT } from '../../utils/scanLifecycleEvent';

const logger = createLogger('useActiveScans');

// Fast while something is unfinished (the user is waiting on it), slow while idle. Scans started
// or finished in this tab don't wait for either: useResumableScan announces them via
// SCAN_LIFECYCLE_EVENT. The idle poll only catches scans started elsewhere (another tab, the
// Telegram bot).
export const ACTIVE_SCANS_POLL_INTERVAL_MS = 10_000;
export const ACTIVE_SCANS_IDLE_POLL_INTERVAL_MS = 60_000;

/** Running/queued scans across every feature, for the AppBar indicator. Paused while hidden. */
export function useActiveScans() {
  const [runs, setRuns] = useState([]);
  const mounted = useRef(true);
  // Refreshes overlap (poll, lifecycle event, tab focus); only the newest request may write, or a
  // slow older response could put a just-finished scan back on the list.
  const latestRequest = useRef(0);

  const refresh = useCallback(async () => {
    const request = ++latestRequest.current;
    try {
      const data = await activityService.listActive();
      if (mounted.current && request === latestRequest.current) setRuns(data);
    } catch (err) {
      logger.warn('Failed to fetch active scans:', err);
    }
  }, []);

  useEffect(() => {
    mounted.current = true;
    refresh();
    const onVisible = () => { if (document.visibilityState === 'visible') refresh(); };
    document.addEventListener('visibilitychange', onVisible);
    window.addEventListener(SCAN_LIFECYCLE_EVENT, refresh);
    return () => {
      mounted.current = false;
      document.removeEventListener('visibilitychange', onVisible);
      window.removeEventListener(SCAN_LIFECYCLE_EVENT, refresh);
    };
  }, [refresh]);

  const isActive = runs.length > 0;
  useEffect(() => {
    const id = setInterval(() => {
      if (document.visibilityState === 'visible') refresh();
    }, isActive ? ACTIVE_SCANS_POLL_INTERVAL_MS : ACTIVE_SCANS_IDLE_POLL_INTERVAL_MS);
    return () => clearInterval(id);
  }, [isActive, refresh]);

  return { runs, refresh };
}
