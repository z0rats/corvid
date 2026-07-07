# OSINT Toolkit — project context

Self-hostable, single-user OSINT/security-analyst web app. FastAPI backend + React frontend, runs via Docker Compose. Not production-hardened (early prototype, per README).

**Maintenance:** update this file after any important project change (new feature, new external dependency, architectural shift). Keep it short and specific — no speculative or redundant detail.

## Stack

- **Backend**: Python 3.14, FastAPI, SQLAlchemy 2.0 (async, `aiosqlite`/`asyncpg`), Alembic migrations, APScheduler for background jobs, `pydantic-ai` for LLM features (Anthropic/OpenAI/Google/Groq/Mistral/xAI/Cohere/Bedrock all wired via `pydantic-ai-slim` extras), `slowapi` for rate limiting, pytest for tests.
- **Frontend**: React 19, MUI 9, Jotai (state), react-router-dom 7, react-scripts 5 (CRA, `--openssl-legacy-provider`), Yarn 4 (berry, `packageManager: yarn@4.15.0`).
- **DB**: SQLite by default at `data/osint_toolkit.db` (see `backend/app/core/config/settings.py` — `DatabaseSettings`, env prefix `DB_`). Logs at `data/logs/`.
- **Deploy**: `docker-compose.yaml` — `backend` (no exposed port, mounts `./data`) + `frontend` (nginx, port 4000). `make up` / `make rebuild` / `make up-backend` / `make up-frontend` (see `Makefile`).

## Backend architecture

Entry point: `backend/main.py` — builds the FastAPI app via `create_fastapi_application()`, lifespan hooks create DB tables, run app defaults, start background favicon fetch, start scheduler.

Layout under `backend/app/`:
- `core/` — cross-cutting: `config/` (settings, CORS, security headers, rate limiting, request-id, body-limit middleware), `settings/` (persisted app settings: `api_keys`, `ai_settings`, `general`, `keywords`, `modules`, `cti_profile` — each has its own models/schemas/crud/routers under `core/settings/<name>/`), `security/ssrf_guard.py` (resolves + validates the hostname of any user-supplied URL before it's fetched server-side, rejecting private/loopback/link-local/reserved IPs, and returns the resolved IP so the caller can pin the request to it and avoid DNS-rebinding — see `newsfeed/utils/favicon_downloader.py`'s `_safe_get` for the pattern; opt-out via `SECURITY_ALLOW_PRIVATE_NETWORK_TARGETS`, dev/testing only), `reports/` (generic HTML/PDF report renderer — `render_html`/`render_pdf` via Jinja2 + `xhtml2pdf`, `generate_report(title, sections, fmt, locale, ...)`; feature-level `report_service.py` modules build `ReportSection`/`ReportRow` lists with their own small `en`/`ru` label dicts and call into this; used by `ioc_lookup` single-lookup history (`GET /api/ioc-lookup/history/{id}/report`) and `email_analyzer` (`POST /api/email/report`, stateless — takes the analysis result in the body since there's no persisted history to fetch by ID; `username_search`'s own export is unrelated — it reuses Maigret's native report generators directly, not this layer), `alerts/` (WebSocket alerts), `database.py`, `scheduler.py`, `dependencies.py`, `exceptions.py`, `healthcheck.py`.
- `features/` — one directory per product feature, each typically split into `routers/`, `service/`, `schemas/`, `models/`, `crud/`, `utils/`, `config/`:
  - `newsfeed/` — RSS aggregation, IOC extraction from articles, MITRE ATT&CK mapping, trends/analytics.
  - `ioc_tools/` — `ioc_lookup` (single + bulk lookups against AbuseIPDB, AlienVault, VirusTotal, Shodan, etc.; single-lookup searches are auto-saved to history once every queried service responds, via `POST/GET/DELETE /api/ioc-lookup/history`, persisted as `SingleLookupSearch`/`SingleLookupResult`), `ioc_extractor`, `ioc_defanger`, `domain_finder` (URLScan.io-based typosquat/phishing domain discovery).
  - `email_analyzer/` — `.eml` parsing, header/IOC checks, AI-assisted analysis.
  - `image_tools/` — EXIF/metadata extraction, hashing, reverse image search deep-links (no API key needed).
  - `llm_templates/` — user-defined AI prompt templates (categories + templates).
  - `cvss_calculator/` — CVSS 3.1/4.0 scoring.
  - `username_search/` — two pluggable sources behind one unified schema (`MaigretSearch`/`MaigretSiteResult`, with a `source` column: `maigret` | `social_analyzer`, and a `extra` JSON column for source-specific display data), selected per-scan via `ScanRequest.source` (`POST /api/username-search/scan`):
    - **maigret** — called in-process (not subprocess) via `maigret.checking.maigret()`, true per-site progress streamed over SSE; settings under `core/settings/username_search/` (timeout/concurrency/top-sites-count/proxy, plus site-database auto-update tracking).
    - **social-analyzer** — invoked as a **subprocess** of its installed CLI (`social_analyzer_service.py`, `--output json`), *not* in-process: the pip package's on-disk module directory is literally named `social-analyzer` (hyphen), which isn't a valid Python identifier, so `import social_analyzer` doesn't work — only `importlib.metadata` (version/site-count) and the console script are usable. No per-site progress callback exists either, so the SSE stream is coarse (`started` → one terminal event); cancellation kills the subprocess. Settings/version-check under `core/settings/username_search/social_analyzer_settings_*` (timeout/top-sites-count, plus a manual PyPI-latest-version check — installing a newer version still requires a container rebuild since site data ships inside the pip package, there's no separate remote DB updater like Maigret's).
    - Report export (`report_service.py`) reuses Maigret's own report writers and only works for maigret-sourced runs; social-analyzer runs just report `has_export: false`.
  - `email_search/` — finds which mail providers a username is registered at, via `mailcat-osint`'s ~26 per-provider checker coroutines (SMTP RCPT probing, provider APIs, registration-form probing, headless Chromium). Driven in-process (no reusable entrypoint exists in mailcat like maigret's, so `service/email_search_service.py` runs the checker coroutines itself, bounded by an `asyncio.Semaphore`), progress streamed over SSE (`POST /api/email-search/scan`), found-provider results persisted (`MailSearch`/`MailSearchResult`). Two checker groups are gated off by default via settings (`core/settings/email_search/`, `enable_smtp_checks`/`enable_headless_checks`): SMTP checkers (Gmail/Yandex/mail.de) need outbound TCP/25 usually blocked in Docker/cloud (workaround: `use_tor`/`proxy_url`, mirroring mailcat's own `--tor`/`--proxy`); headless-Chromium checkers (Fastmail/int.pl/onet.pl, via `requests-html`→`pyppeteer`) lazily download a Chromium binary on first real use. Like social-analyzer, version/update-check is a manual PyPI-latest check (`GET /api/email-search/info`, `POST /api/email-search/check-update`) — installed version read from package metadata (no `__version__` attribute on the `mailcat` module itself), latest-available version persisted on `EmailSearchConfig`; installing a newer version still requires a container rebuild.
- All routers are aggregated in `backend/app/utils/router_registry.py` via `get_core_routers()`, `get_settings_routers()`, `get_feature_routers()`, then mounted in `main.py`.
- Migrations: Alembic, config at `backend/alembic.ini`, scripts in `backend/migrations/versions/`. Run after schema changes: `docker compose run --rm backend alembic upgrade head`.
- Tests: `backend/tests/`, run with pytest (`pytest.ini` sets `testpaths = tests`, `pythonpath = .`). Currently sparse coverage (only `tests/features/image_tools`).

## Frontend architecture

`frontend/src/features/` mirrors the backend feature split — one directory per module (`newsfeed`, `ioc-tools`, `email-analyzer`, `image-tools`, `llm-templates`, `cvss-calculator`, `rule-creator` (Sigma/Yara/Snort rule builder), `username-search`, `email-search`, `settings`). Each feature dir typically has its own `components/`, `hooks/`, `services/` (API calls), `constants/`, `utils/`. Entry: `src/App.js` → `src/index.js`. `src/core/` holds shared/cross-feature code.

New top-level features need edits in three places beyond their own directory: `src/core/config/routes.js` (lazy route), `src/core/config/sidebarConfig.js` (nav entry + tabs config), and `src/core/components/layout/Layout.jsx` (`currentTabs` path match for the new tabs getter). i18n: add a `<featureName>.json` under both `src/core/i18n/locales/en/` and `ru/`, register in `src/core/i18n/index.js`, and add `nav.*` keys to `common.json` (both locales).

## Integrated external services

IOC/threat-intel lookups across IPs, domains, URLs, emails, hashes, CVEs via: AbuseIPDB, AlienVault OTX, CheckPhish, CrowdSec, GitHub, Google Safe Browsing, HIBP, Hunter.io, IPQualityScore, Maltiverse, NIST NVD, Pulsedive, Reddit, Shodan, ThreatFox, Twitter/X, URLScan.io, VirusTotal. API keys configured per-service in app settings (`core/settings/api_keys/`), not via `.env` for these.

## Conventions worth knowing

- Settings/config uses `pydantic-settings` with per-domain `BaseSettings` subclasses, each with its own `env_prefix` (e.g. `DB_`, `LOG_`, `API_`, `SCHEDULER_`), all loaded from a single `.env` (gitignored, not present in repo — none committed).
- In route handlers, prefer injecting settings via dependency (`SettingsDep`) rather than importing the module-level `settings` singleton, so tests can override via `app.dependency_overrides`.
- Feature module layering pattern: `routers` (HTTP) → `service` (business logic) → `crud` (DB access) → `models`/`schemas`. New features should follow this same split.
- AGPL-3.0 licensed (versions ≤ v0.1.0 are MIT). Be mindful of this when adding dependencies or discussing licensing.
- Any code that makes an HTTP request to a URL/host supplied (directly or indirectly) by the user must go through `core/security/ssrf_guard.py` first (see `favicon_downloader.py`) — otherwise it's an SSRF vector into the docker network, localhost, or cloud metadata endpoints.
- `backend/requirements.txt` is compiled (pip-compile/`uv pip compile` style, hand-merged since no `requirements.in` is committed) — `maigret` declares `lxml>=6.0.2` but `newspaper4k` pins `lxml<6.0.0`; resolved via `backend/lxml-override.txt` (`lxml==5.4.0`, passed as `--override` in `Dockerfile`) since maigret doesn't actually import lxml directly. Don't bump lxml without re-checking this (`social-analyzer` also declares an unpinned `lxml` dependency but likewise never imports it directly — verified compatible with the same override; `mailcat-osint`'s `requests-html`→`pyppeteer` chain was also verified compatible with the same override, no additional pin needed).

## Useful commands

- `make up` / `make rebuild` — start (or rebuild + start) full stack via Docker.
- `make up-backend` / `make rebuild-backend`, `make up-frontend` / `make rebuild-frontend` — per-service.
- `docker compose run --rm backend alembic upgrade head` — apply DB migrations.
- Backend tests: `cd backend && pytest`.
- Frontend dev: `cd frontend && yarn start` (uses `--openssl-legacy-provider`); build: `yarn build`; test: `yarn test`.
- App served at `http://localhost:4000` once containers are up.
