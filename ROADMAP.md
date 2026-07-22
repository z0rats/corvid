# Corvid — Improvement Roadmap

Ideas for hardening the project across four angles: performance, UI/UX, security, and resilience (fault tolerance) —
plus a backlog of new OSINT capabilities: tool/site integrations, cross-feature data aggregation, and routine automation.
This is a backlog, not a commitment — pick items opportunistically. Grounded in the current architecture described in `CLAUDE.md`; re-check file/line references before acting since the code will keep moving.

Effort tags: **S** = small/quick win, **M** = medium, **L** = larger effort/design work.

## New OSINT Features

Ideas for expanding investigative capability itself, rather than hardening what already exists.

### Tool & site integrations

- **[M] Wayback Machine / archive.org integration.** Given a URL or domain, pull the list of archived snapshots (`web.archive.org/cdx/search/cdx`) and let the analyst open a historical snapshot — useful for viewing a phishing page's content after it's been taken down. Fits as a `domain_finder` panel or a standalone small feature; must go through `ssrf_guard.safe_get` like every other outbound fetch, since the target URL is user-supplied.
- **[M] Finish wiring Censys.** `ioc_tools/ioc_lookup/config/rate_limiting_config.py` already reserves a rate-limit slot for Censys, but no provider function is actually registered anywhere in `ioc_lookup`. Add the API client (host/certificate search) alongside Shodan in `external_api_clients.py` and register it in `service_registry.py` for IP/domain lookups.
- **[L] Breach/leak search beyond HIBP.** Current email-breach coverage is HIBP only (one of several email providers in `ioc_lookup`). Add DeHashed and/or LeakCheck/IntelligenceX as additional providers — these also support username/domain/password-hash search, which HIBP doesn't. Could extend `ioc_lookup`'s email type, or become a small dedicated "breach search" feature reusing the same `routers`/`service`/`crud` layering as other features.
- **[M] Paste-site monitoring using the existing keyword list.** `core/settings/keywords/` is currently consumed only by `newsfeed/service/feed_processing_service.py` to flag relevant articles. Add a scheduled job (same APScheduler pattern newsfeed already uses) that periodically queries a paste-site search API (e.g. PSBDMP, or Pastebin's paid scraping API) for the same keyword list and surfaces hits the same way newsfeed does — reuses an existing settings module instead of introducing a new one.

### Data aggregation

- **[L] "Investigation" / target-profile entity.** The biggest structural gap: `username_search`, `email_search`, `reddit_search`, `ioc_lookup`, and `email_analyzer` each persist their own independent history table, with nothing tying them together. Introduce an `Investigation` model (id + label + created_at + a loose set of linked search IDs across the existing history tables) so an analyst can group "everything found about this username/email/domain" into one view, and generate a single combined report via the existing generic `core/reports/` renderer instead of separate per-feature reports.

### Routine automation

- **[L] Watchlist / recurring re-scan with alerts.** Every current scan (username_search, email_search, ioc_lookup, reddit_search) is one-shot and manual. Reuse newsfeed's per-feed APScheduler + health-tracking pattern to let an analyst pin a username/domain/IOC to a recurring interval, diff new results against the last run, and push a notification through the existing `alerts/` WebSocket when something new shows up — turns the tool from "look it up now" into "tell me when it changes."

## Performance

## UI/UX

## Resilience / Fault tolerance
