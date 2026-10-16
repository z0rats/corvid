import { useCallback, useEffect, useRef, useState } from 'react';
import { activityService } from '../../services/api/activityService';
import { createLogger } from '../../utils/logger';

const logger = createLogger('useActiveScans');

export const ACTIVE_SCANS_POLL_INTERVAL_MS = 10_000;

/**
 * Running/queued scans across every feature, for the AppBar indicator. Polled (like useAlerts)
 * and paused while the tab is hidden; a shorter interval than alerts since a scan finishing is
 * what the user is waiting on.
 */
export function useActiveScans() {
  const [runs, setRuns] = useState([]);
  const mounted = useRef(true);

  const refresh = useCallback(async () => {
    try {
      const data = await activityService.listActive();
      if (mounted.current) setRuns(data);
    } catch (err) {
      logger.warn('Failed to fetch active scans:', err);
    }
  }, []);

  useEffect(() => {
    mounted.current = true;
    refresh();
    const id = setInterval(() => {
      if (document.visibilityState === 'visible') refresh();
    }, ACTIVE_SCANS_POLL_INTERVAL_MS);
    const onVisible = () => { if (document.visibilityState === 'visible') refresh(); };
    document.addEventListener('visibilitychange', onVisible);
    return () => {
      mounted.current = false;
      clearInterval(id);
      document.removeEventListener('visibilitychange', onVisible);
    };
  }, [refresh]);

  return { runs, refresh };
}
