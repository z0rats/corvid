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

Key test: `routers/key_test_routes.py` (`POST /api/services/{service}/test`, `POST
/api/services/test`, 10/min) runs `service/key_test_clients.py`'s per-service check on the saved
key(s) and returns `KeyTestResult` (`ok|rejected|rate_limited|plan_required|unreachable|error|
not_configured|untestable`, HTTP status, our own `detail`, optional `quota`). A check spends nothing
from a counted allowance (account/status/token endpoint, or a lookup on a quota-free provider);
the rest sit in `KEY_TEST_EXEMPT` with a reason, exposed as `key_test_exempt_reason` in the services
config (`docs/adr/0026-api-key-test-free-calls-only.md`). `test_key_test_registry.py` fails on a
keyed service in neither. Results are live only; the frontend auto-tests after a save.

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

## `backup/`

Full app-state export/import, SQLite only (`get_backup_status` reports `supported: false` for any
other dialect). `POST /api/backup/export` takes a consistent snapshot via `VACUUM INTO` (no
separate `-wal`/`-shm` sidecars needed, unlike a raw file copy), tars it with `.encryption_key`
and — only if `include_access_token` is set — `.access_token`, plus a `manifest.json` (app
version, dialect, the DB's stamped Alembic revision). Optionally wraps the whole archive with a
Fernet key derived from a user passphrase via PBKDF2-HMAC-SHA256; restore auto-detects an
encrypted archive by its missing gzip magic bytes rather than needing a separate flag.

`POST /api/backup/restore` validates the manifest (dialect match, a recognized Alembic revision)
and the extracted DB (`PRAGMA integrity_check`) before swapping files into place via `os.replace`
— an atomic rename, so the *currently running* process's already-open connections keep working
against the pre-restore file (same inode) until the operator restarts the backend. No in-process
engine hot-swap; see `docs/adr/0010-backup-restore-design.md` for why. Requires a `confirm:
"RESTORE"` form field, checked before any file is touched.

## `alerts/`, `database.py`, `scheduler.py`, `exceptions.py`

`alerts/` is WebSocket alerts (see Access control below for its token-check exemption)
plus, via `alerts_service.raise_alert`, best-effort Telegram delivery and the shared hook
points in `scans/run.py`/`scheduler.py` that call it — see
`docs/architecture/notifications.md`. `database.py`/`exceptions.py` are otherwise
unremarkable — standard DB session setup and the shared `AppHTTPException` hierarchy.

## `dependencies.py`

Includes `get_disk_space_health` — warns at `"low"` below
`AppSettings.low_disk_space_threshold_bytes` (env `LOW_DISK_SPACE_THRESHOLD_BYTES`, default
1 GiB) free on `data_dir`. Logged once at startup via `main.py`'s `_check_disk_space` and
re-checked on every `/api/healthcheck/detailed` call.

## `healthcheck.py`

Basic/detailed/`ready`/`live` probes. Detailed status is `"degraded"`, not `"unhealthy"`, when
only disk is low — a low-disk warning shouldn't read as a hard outage to monitoring.

## Access control (`security/access_control.py`)

No user accounts (single-user tool): every `/api/*` route plus `/openapi.json` is behind one shared
bearer token (`verify_access_token`, a router-level dependency in `utils/router_registry.py`). The
token comes from `API_ACCESS_TOKEN` or is auto-generated and persisted to `<data_dir>/.access_token`
(0600, `persisted_secret.py`), printed once at startup. `POST /api/settings/access-token/regenerate`
(`core/security/routes.py`, Settings -> About) rotates it immediately, unless `API_ACCESS_TOKEN`
pins it. `router_registry.get_public_routers()` lists the only unguarded routers: healthcheck, the
alerts `ws_router` (checks the token via `?token=`, since a WS handshake can't carry a custom
header) and newsfeed feed icons (`<img src>`, same limitation). `/docs`/`/redoc` are public
data-free shells that fetch the guarded `/openapi.json` with the SPA's token
(`core/config/docs_pages.py`, non-production only).

## Security headers

Set in two places, since the backend never sees the SPA's response: `config/security_config.py`'s
`SecurityHeadersMiddleware` covers `/api/*`, `/docs`, `/redoc`, `/openapi.json` (CSP relaxed for
`cdn.jsdelivr.net` + an inline init script on `/docs`/`/redoc` only - static shells with no user
content); `frontend/nginx.conf`'s `location /` sets the same base headers plus a strict CSP for the
SPA. HSTS is production-only (`ENVIRONMENT=production`), never sent over plain HTTP.

## Log redaction (`config/log_redaction.py`)

`SecretRedactionFilter` is on every logging handler (`logging_config.py`) and scrubs API-key-shaped
substrings (query params, `Bearer` tokens, IPQualityScore's path-embedded key) from every record.
Several IOC providers (Hunter.io, Pulsedive, Shodan, Google Safe Browsing, IPQualityScore) put the
key in the URL and `httpx.HTTPStatusError`'s `str()` embeds it. Pattern-based, so new providers
are covered.

## File uploads (`utils/file_upload.py`)

Shared read-validate-dispatch shape for upload endpoints (`image_tools`, `email_analyzer`):
`validate_uploaded_file(file, *, no_file_code, read_error_code, validate_fn)` reads and validates
against the feature's own `validate_file_upload(filename, size) -> (is_valid, error_code,
error_message)`, returning raw bytes or raising a 400 `AppHTTPException`.
`run_file_endpoint(service_fn, *args, error_code, failure_message, value_error_code=None,
run_in_thread=True)` dispatches the service call (via `asyncio.to_thread` unless
`run_in_thread=False`, for an already-async `service_fn`) and maps `ValueError`/other exceptions
to a 422.

## `registry_dumps/`

`common.py`/`scheduler.py`: the shared "download -> validate -> all-or-nothing table replace ->
provenance row -> staleness-driven refresh" plumbing behind every locally cached list dump
(`ru_business_check`'s three, `sanctions_search`'s one). A new dump-backed feature adds a thin
`dump_jobs()`/`register_*_scheduler()` wrapper (see
`ru_business_check/service/registry_dump_scheduler_service.py`).
