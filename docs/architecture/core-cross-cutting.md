# `backend/app/core/` — cross-cutting concerns

Deep-dive referenced from AGENTS.md's Backend architecture section. Covers subsystems shared
across every feature module.

## `config/`

Settings, CORS, security headers, rate limiting, request-id, body-limit middleware. See
`Conventions worth knowing` in AGENTS.md for the `pydantic-settings` per-domain pattern.

## `settings/`

Persisted app settings. Each domain (`api_keys`, `ai_settings`, `general`, `keywords`, `modules`,
`cti_profile`) has its own models/schemas/crud/routers under `core/settings/<name>/`.

**`api_keys`**: `Apikey.key` is encrypted at rest via `EncryptedString`/`secrets_crypto.py`
(Fernet). The key comes from `SECURITY_ENCRYPTION_KEY` or is auto-generated at
`<data_dir>/.encryption_key` (0600 permissions) — back that file up alongside the DB, since
losing it makes every stored key unrecoverable. Legacy plaintext rows still read fine and get
encrypted transparently on next save (no migration step needed).

A live quota panel lives at `routers/quota_routes.py`'s `GET /api/services/quota`, hitting
VirusTotal/Shodan/Hunter.io's own quota endpoints with the stored key — currently the only three
wired providers that expose one.

## `security/ssrf_guard.py`

Resolves and validates the hostname of any user-supplied URL before it's fetched server-side,
rejecting private/loopback/link-local/reserved IPs.

`safe_get(client, url, ...)` is the single shared entrypoint. It pins the resolved IP for the
request *and* manually re-validates each redirect hop, since httpx's own `follow_redirects` would
re-resolve `Location` without going through this check — callers must therefore construct their
`httpx.AsyncClient` with `follow_redirects=False`.

Covers every feature that fetches a user-supplied or externally-sourced URL over `httpx`: favicon
downloads, newsfeed article/feed fetching, LLM-template web content, domain WHOIS/RDAP redirects.
Opt-out via `SECURITY_ALLOW_PRIVATE_NETWORK_TARGETS`, dev/testing only.

`git_recon`'s repo-clone target is the one outbound-fetch path *not* on `httpx` in this codebase
— see `docs/architecture/git-recon.md` for the subprocess-argv allowlist that plays the same role
there. `tests/core/test_ssrf_guard_coverage.py` fails on any new raw `httpx`/`requests` client
that isn't on its reviewed fixed-host allowlist.

## `reports/`

Generic HTML/PDF report renderer — `render_html`/`render_pdf` via Jinja2 + `xhtml2pdf`,
`generate_report(title, sections, fmt, locale, ...)`. Feature-level `report_service.py` modules
build `ReportSection`/`ReportRow` lists and call into this.

`ReportRow.href` (optional) renders the row's value as a clickable link in both the HTML output
and the PDF — xhtml2pdf renders `<a href>` as a real clickable PDF link/`~URI` annotation.

Used by:
- `ioc_lookup` single-lookup history (`GET /api/ioc-lookup/history/{id}/report`, `en`/`ru` label
  dicts).
- `email_analyzer` (`POST /api/email/report`) — stateless, takes the analysis result in the
  request body since there's no persisted history to fetch by ID; `en`/`ru` label dicts.
- `ru_business_check` (`GET /api/ru-business-check/history/{id}/report`) — Russian-only
  hardcoded per that feature's own convention. Every row with a specific per-request source URL
  (an arbitration case, a Федресурс/Прозрачный бизнес/РНП profile, a WHOIS/RDAP or Wayback
  lookup) links there directly rather than to the source's homepage. Frontend downloads via an
  authenticated blob fetch (`ruBusinessCheckApi.exportReport`), not a plain `<a href>`, since
  every `/api/*` route needs the `Authorization` header a bare anchor can't attach.

## `alerts/`, `database.py`, `scheduler.py`, `exceptions.py`

`alerts/` is WebSocket alerts (see Access control in AGENTS.md for its token-check exemption).
The other three are unremarkable — standard DB session setup, APScheduler wiring, and the shared
`AppHTTPException` hierarchy.

## `dependencies.py`

Includes `get_disk_space_health` — warns at `"low"` below
`AppSettings.low_disk_space_threshold_bytes` (env `LOW_DISK_SPACE_THRESHOLD_BYTES`, default
1 GiB) free on `data_dir`. Logged once at startup via `main.py`'s `_check_disk_space` and
re-checked on every `/api/healthcheck/detailed` call.

## `healthcheck.py`

Basic/detailed/`ready`/`live` probes. Detailed status is `"degraded"`, not `"unhealthy"`, when
only disk is low — a low-disk warning shouldn't read as a hard outage to monitoring.
