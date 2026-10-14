# In-app alerts inbox polls the unread count instead of using the /ws/alerts WebSocket

`raise_alert` persists every alert and broadcasts it to `/ws/alerts` clients. The frontend had no
consumer of either, so alerts (scan outcomes, failing jobs, security events such as repeated
failed-auth attempts) were invisible unless Telegram was configured.

## Decision

The AppBar bell (`core/components/ui/AlertsMenu.jsx`, `core/hooks/api/useAlerts.js`) polls
`GET /api/alerts/count/unread` every 30 s while the tab is visible (and on refocus), and loads the
list over REST when opened.

- **Not the WebSocket.** `frontend/nginx.conf` proxies only `/api/`, `/docs`, `/openapi.json`; the
  docker deployment has no `/ws/` route, so a socket client would work in `yarn start` and silently
  never connect in production. Adding the route means `Upgrade`/`Connection` headers, longer proxy
  timeouts, and reconnect/backoff logic in the client - for a single-user tool where a ≤30 s delay
  on an alert costs nothing.
- **Cost.** One tiny indexed `COUNT` query per 30 s per open tab; paused while the tab is hidden.
- `/ws/alerts` stays as-is (token-checked, unused by the bundled UI) - available if live push is
  ever worth the proxy work, at which point polling becomes the fallback.

Alert deep links reuse the scan alert's `Scan #<id>` message prefix (`core/scans/run.py`) and the
`module` name, mapped to routes in `core/utils/alertLink.js` / `historyPaths.js`.
