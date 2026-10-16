// Window event fired by useResumableScan when a scan in this tab starts, is queued for or gets a
// heavy-scan slot, or reaches a terminal state, so the AppBar's active-scans indicator refreshes
// at once instead of on its next poll. `queued`/`running` matter because `started` arrives before
// the backend has put a heavy run in its queue, so that refresh alone would still say Running.
export const SCAN_LIFECYCLE_EVENT = 'corvid:scan-lifecycle';

const LIFECYCLE_TYPES = new Set(['started', 'queued', 'running', 'completed', 'cancelled', 'failed']);

export function announceScanLifecycle(eventType) {
  if (LIFECYCLE_TYPES.has(eventType)) window.dispatchEvent(new Event(SCAN_LIFECYCLE_EVENT));
}
