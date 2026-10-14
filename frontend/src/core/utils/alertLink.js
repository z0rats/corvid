import { getRunPath } from './historyPaths';

// Alert `module` values (backend raise_alert callers) -> where in the app the alert points.
// Scan alerts are raised by core/scans/run.py with the ScanFeature/source name as module and
// "Scan #<id> ..." as message, so they can deep-link straight to that run's history page.

const MODULE_PATHS = {
  security: '/settings/about',
  api_keys: '/settings/apikeys',
  backup: '/settings/backup',
  newsfeed: '/newsfeed',
};

const SCAN_ID_RE = /^Scan #(\d+)\b/;

/** The in-app path an alert should open on click, or null when it has nowhere to go. */
export function getAlertLink(alert) {
  const match = SCAN_ID_RE.exec(alert.message ?? '');
  const runPath = getRunPath(alert.module, match ? match[1] : null);
  if (runPath) return runPath;
  return MODULE_PATHS[alert.module] ?? null;
}
