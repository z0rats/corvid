# Corvid — project context

Self-hostable, single-user OSINT/security-analyst web app. FastAPI backend + React frontend, runs via Docker Compose. Early prototype, not production-hardened.

Where things live: user-facing behaviour and deployment in `README.md` and the docs site (`website/`); configuration in `.env.example`; the reasons behind choices in `docs/adr/`; undecided product questions in `docs/open-questions.md`; implementation detail in `docs/architecture/<slug>.md`; review checklists in `docs/review-areas.md`.

**Maintenance:** this file loads in full on every message regardless of task, so its size is a standing tax on every conversation. It is a map, not the deep info itself.

- Update it after any important project change (new feature, new external dependency, architectural shift) as a *net* pass: prune or tighten roughly as much as you add. Past ~25KB, condense before adding.
- A feature gets one line here plus a `Deep-dive: docs/architecture/<slug>.md` pointer once its detail outgrows a sentence or two.
- Current state only: no history, no "see commit/PR #123", no incident narratives. A short present-tense reason clause ("X, since Y") is fine.
- Big decisions (dependency choice, storage tradeoff, one approach over a real alternative) go in a new `docs/adr/NNNN-*.md` in `docs/adr/TEMPLATE.md`'s format (`test_adr_format.py` requires `## Decision` and `## Rejected` from 0023 on). A flipped decision supersedes the old ADR, never rewrites it.
- Never cite an uncommitted plan/spec/audit file. Drift gates: `scripts/check_doc_references.py` (dangling `docs/*.md` refs), `.github/scripts/check-docs-coverage.mjs` (feature pages, scan `source` values, Settings tabs), `backend/tests/core/test_env_docs_sync.py` (env vars).
- Update `README.md` for user-facing changes, especially deployment (setup steps, env vars, `.env`/`docker-compose.yaml` behaviour).

## Rules

- **Git:** run `git commit` / `git push` (or tags, releases) ONLY when the user directly asks for that specific action. A broader instruction ("update the repo", "ship this", "fix everything") does not count. Approval to commit is not approval to push, or to commit again later.
- **Before a feature** that changes what the user sees or what is stored, list what is still undecided and settle it with the owner first (process: `docs/open-questions.md`). Don't settle product questions silently in code.
- New or substantially changed feature logic ships with tests in the same change - Codecov has no failing threshold, so nothing else catches untested code.
- Review a change in a fresh session, not the one that wrote it, against the matching sections of `docs/review-areas.md`. A bug class that ships past review earns an item there. After fixing a bug, prefer a structural test/gate that makes the whole class impossible (e.g. `tests/core/test_ssrf_guard_coverage.py`).
- Minimize new dependencies - implement small pieces ourselves; a dependency only for genuinely non-trivial functionality (crypto, parsing, protocols) or a de facto standard in this stack. AGPL-3.0 licensed (≤ v0.1.0 MIT) - mind it when adding one.
- Complexity budget: a file near ~1000 lines, or a function over ~150 lines / 8 parameters, is a prompt to decompose.

## Stack

- **Backend**: Python 3.14, FastAPI, SQLAlchemy 2.0 async (`aiosqlite`), Alembic, APScheduler, `pydantic-ai-slim[anthropic,openai]` (+ local Ollama discovery), `slowapi`, pytest. SQLite only - a non-SQLite `DB_URL` fails at startup (`docs/adr/0004-sqlite-only-postgres-unsupported.md`); DB at `data/corvid.db`, logs at `data/logs/`.
- **Frontend**: React 19, MUI 9, Jotai, react-router 8 (declarative, imports from `react-router`), Vite + Vitest (jsdom), ESLint 10 flat config, Yarn 4. TypeScript adopted incrementally (`allowJs`, convert-on-touch), pinned `~6.0.3`.
- **Deploy**: `docker-compose.yaml` — `backend` (no exposed port, mounts `./data`, loads root `.env` via `env_file`) + `frontend` (nginx, port 4000). `docker-compose.prod.yaml` (installer) pins images via `CORVID_VERSION` (`update.sh [version]`).
- Pins, CI, release, dependabot, pre-commit, coverage, lock files, docs site: `docs/architecture/tooling.md`.

## How it runs

- `backend/docker-entrypoint.py` starts as root only to `chown` the bind-mounted `./data`, drops to `appuser` (UID 1000), runs `alembic upgrade head` (a failed migration aborts startup), then `execvp`s uvicorn. Tool state under `appuser`'s home (maigret DB, pyppeteer Chromium, subfinder config, amass engine DB) is build-time and resets on container recreate; scan results persist in the DB.
- `backend/main.py`'s lifespan: `Base.metadata.create_all()` (what bootstraps local dev without migrations), app defaults, one background task running the post-startup catch-ups sequentially (`_STARTUP_CATCHUPS`: favicons, blacklist, registry dumps - sequential because SQLite has one writer), the APScheduler scheduler, and the Telegram bot polling loop (`docs/adr/0012-telegram-bot-polling.md`).
- Scheduler jobs are in-memory: an `IntervalTrigger` countdown resets on every restart (no persistent job store), so a job whose data goes stale needs a startup catch-up that derives staleness from the DB (e.g. `blacklist_refresh_service.is_blacklist_stale`), not just an empty-table check.
- Scans run as background tasks in the backend process (some shell out to CLI tools), streamed over SSE; heavy ones queue behind `SCAN_MAX_CONCURRENT_HEAVY` slots. `ScanRun.is_queued` is in-memory only; unfinished runs are reconciled at startup (see Conventions).
- Migrations: Alembic (`backend/alembic.ini`, `backend/migrations/versions/`), history squashed to one base revision (`docs/adr/0001-squash-migration-history.md`); manual run: `docker compose run --rm backend alembic upgrade head`.

## Backend architecture

`backend/app/`: `core/` (cross-cutting), `features/` (one dir per product feature, split `routers/` → `service/` → `crud/` → `models/`/`schemas/`, plus `utils/`, `config/`), `utils/router_registry.py` (all routers via `get_core_routers()`/`get_settings_routers()`/`get_feature_routers()`, mounted in `main.py`).

- `core/` — `config/`, `settings/`, `security/`, `reports/`, `alerts/`, `backup/`, `telegram_bot/`, `registry_dumps/` (shared plumbing for locally cached list dumps), `external_sources/` (response-shape guard, `docs/adr/0022-external-source-contract.md`), `scans/`, `database.py`, `scheduler.py`. Deep-dive: `docs/architecture/core-cross-cutting.md` (also access control, security headers, log redaction, upload helpers); alerts: `docs/architecture/notifications.md`; backup: `docs/adr/0010-backup-restore-design.md`.
- **Access control**: no user accounts; one shared bearer token (`core/security/access_control.py`'s `verify_access_token`, router-level) guards every `/api/*` route and `/openapi.json`. From `API_ACCESS_TOKEN` or auto-generated into `<data_dir>/.access_token`. Unguarded routers are listed in `router_registry.get_public_routers()`.

Features (`backend/app/features/`):

- `newsfeed/` — RSS aggregation, article IOC extraction, MITRE ATT&CK mapping, trends, per-feed health and Admiralty reliability grades. Deep-dive: `docs/architecture/newsfeed.md`.
- `ioc_tools/` — `ioc_lookup` (single + bulk lookups against ~30 providers, plus a keyless local `blacklist` for EVM/Bitcoin addresses), `ioc_extractor`, `ioc_defanger`, `domain_finder` (typosquat discovery plus subdomain/DNS/history/host-probe panels). Deep-dive (incl. provider list): `docs/architecture/ioc-tools.md`.
- `email_analyzer/` — `.eml` parsing, header/IOC checks, AI-assisted analysis.
- `image_tools/` — EXIF/metadata, hashing, reverse-search links, AI geolocation hypothesis, GPS tools, ChronoVerify. Deep-dive: `docs/architecture/image-tools.md`.
- `llm_templates/` — user-defined AI prompt templates. `cvss_calculator/` — CVSS 3.1/4.0.
- `username_search/` — maigret, social-analyzer and `threat_actor_usernames` behind one schema, one scan per source. Deep-dive: `docs/architecture/username-search.md`.
- `email_search/` — mailcat-osint providers, GHunt Google profile (isolated venv, `docs/adr/0018-isolated-tool-cli-venvs.md`), `user_scanner` (`docs/adr/0019-user-scanner-email-source.md`). Deep-dive: `docs/architecture/email-search.md`, `docs/architecture/ghunt.md`.
- `phone_search/` — one E.164 number's registration on Amazon/Microsoft/Facebook, in-house checkers, no bulk by design (`docs/adr/0016-phone-search-in-house-checkers.md`).
- `reddit_search/` — a user's full history incl. removed content (Arctic Shift + PullPush). Deep-dive: `docs/architecture/reddit-search.md`.
- `dork_runner/` — parameterized dork templates, DuckDuckGo by default. Deep-dive: `docs/architecture/dork-runner.md`.
- `youtube/` — video metadata (keyless) plus counts/comments with a Data API key. Deep-dive: `docs/architecture/youtube.md`.
- `instagram_search/` — profile metadata via `instaloader` plus a followers/posts scan; optional imported session cookie, never a password. Deep-dive: `docs/architecture/instagram-search.md`.
- `git_recon/` — gitcolombo in-process; `git clone` subprocess gated by `validate_github_repo_url`. Deep-dive: `docs/architecture/git-recon.md`.
- `amass/` — OWASP Amass v5 with its engine as a background subprocess (`docs/adr/0013-amass-engine-in-container.md`). Deep-dive: `docs/architecture/amass.md`.
- `ru_business_check/` — Russian due diligence by ИНН/name: live registries plus scheduled dumps into one risk engine; a failed or drifted source is "not checked", never empty; Russian-only UI by design. Deep-dive: `docs/architecture/ru-business-check.md`.
- `sanctions_search/` — free-text search over the full OFAC SDN list from a local OpenSanctions dump (`docs/adr/0017-sanctions-search-opensanctions-and-in-house-matching.md`).
- `steam_recon/` — profile lookup plus friends-graph scan, Steam Web API key required, clean-room heuristics (`docs/adr/0015-steam-recon-clean-room-and-heuristic-scoring.md`). Deep-dive: `docs/architecture/steam-recon.md`.
- `activity/` — read-only `GET /api/activity` (newest runs across every `ScanFeature` plus IOC-lookup/Reddit history, start screen) and `GET /api/activity/active` (unfinished runs, AppBar indicator).

## Frontend architecture

`frontend/src/features/` mirrors the backend split (kebab-case), plus `rule-creator` (frontend-only) and `settings`; each has `components/`, `hooks/`, `services/`, `constants/`, `utils/`. Entry `src/App.jsx` → `src/index.jsx`; shared code in `src/core/`.

- MUI 9's `Box`/`Stack`/`Grid` style only through `sx` - top-level shorthand props are silently inert; ESLint blocks them (`docs/adr/0009-mui-box-shorthand-props-removed.md`).
- i18n: `src/core/i18n/` (`en`/`ru`, one JSON per namespace, auto-discovered from `locales/en/<camelCase>.json`). New keys English-only unless `ru` is asked for. Batch translation via subagents: point them at `frontend/I18N_PATTERN.md`.
- **New top-level features** also need: a `featureRoutes.js` entry; a `MAIN_MENU_ITEMS_CONFIG` entry in `sidebarConfig.jsx` (`section`, `aliases`/`tags`/`accepts` - the command palette derives from it); for sub-tabs a tabs config + `TAB_ROUTES` entry; a `utils/historyPaths.js` entry (scan features); a `router_registry.py` entry; a `website/` stub page under `features/`. `.github/scripts/check-feature-completeness.mjs` (+ `check-docs-coverage.mjs`) fails CI per missing item; deliberate gaps go in its `EXEMPT` map. Pages title themselves via `core/components/ui/PageHeader`.
- **Command palette** (`/` or `⌘K`): `core/utils/commandParser.ts` plus a JS port of backend IOC detection synced via a shared fixture. "Send to X" and `value tool` pivots prefill via `?q=` - a new single-value identity feature must wire it or the pivot silently drops the value. Deep-dive: `docs/architecture/command-palette.md`.

## Docs site and extension

- `website/` — public docs (`https://z0rats.github.io/corvid/`, Astro + Starlight), the deep reference for every feature and setting; `README.md` stays a short pitch linking to it. Ground pages in the source (routers/schemas), never link an external URL you haven't confirmed. Details: `docs/architecture/tooling.md`.
- `extension/` — MV3 Chrome "Quick Send": selection popup, context menu and side panel funnel into `<base_url>/ioc-tools/lookup?q=...`. `ioc-type-detection.js` and its reverse-search list are hand-duplicated from the frontend - re-check by hand when either changes. Deep-dive: `docs/architecture/browser-extension.md`.

## Conventions worth knowing

- Settings: `pydantic-settings`, one `BaseSettings` per domain with its own `env_prefix` (`DB_`, `LOG_`, `API_`, `SCHEDULER_`, ...), all from one gitignored `.env`. In route handlers inject `SettingsDep` rather than importing the `settings` singleton, so tests can override it.
- **SSRF:** any HTTP request to a user-supplied (directly or indirectly) URL/host goes through `core/security/ssrf_guard.py`'s `safe_get`; `tests/core/test_ssrf_guard_coverage.py` fails on a new raw `httpx`/`requests` client not on its fixed-host allowlist. Every external source also needs a `Covered`/`Exempt` entry in `tests/canary/coverage_map.py` (gate: `tests/core/test_canary_coverage.py`).
- **Source drift:** a parser raises `SourceDriftError` (`core/external_sources/contract.py`'s `require_*`) on a changed shape and returns empty only for a legitimately empty answer. `domain_finder` surfaces it as `<CODE>_SCHEMA_DRIFT`; `ioc_lookup` providers declare `ProviderSpec.expects` or a reasoned exemption. A new source needs a drift case.
- **New `ioc_lookup` provider:** update `website/src/content/docs/features/ioc-tools.md` in the same change (pre-commit gate); a keyed provider takes `supported_ioc_types` from `service_config.py`'s `ServiceDefinition`.
- **External tool versions:** any tool behind a UI feature is pinned and exposes its installed version - `requirements.txt` (Python), the Dockerfile (binaries, exact tag, not `@latest`), or an isolated venv (`docs/adr/0018-isolated-tool-cli-venvs.md`). Read via `importlib.metadata` or `core/utils/cli_tool_version.py`'s `get_cli_tool_version`; latest-on-PyPI via `pypi_version_check.py`. Updating needs a container rebuild.
- **Scans:** one `core/scans/feature.py` `ScanFeature` per scan table, history routes via `core/scans/routes.py`'s `add_run_routes`, registered in `utils/scan_reconciliation_registry.py` (test-enforced; else runs stay `running` after a restart) with a `target_column`. Heavy runs pass `heavy=True` and start subprocesses inside `run_work`. Frontend: `core/hooks/useResumableScan`, `core/components/HistoryTable`/`HistoryDetailHeader`. All SSE via `core/scans/sse.py`'s `sse_stream` / `core/services/sseStream.ts`. Deep-dive: `docs/architecture/scan-lifecycle.md`.
- **Notifications:** a new notification-worthy event calls `core/alerts/service/alerts_service.py`'s `raise_alert()` (in-app bell, polled - `docs/adr/0020-alerts-inbox-polling.md` - plus optional Telegram). Deep-dive: `docs/architecture/notifications.md`.
- **Secrets in logs:** `core/config/log_redaction.py`'s filter scrubs key-shaped substrings on every handler, pattern-based, so new providers are covered.
- **Uploads:** new upload endpoints use `core/utils/file_upload.py`'s `validate_uploaded_file` / `run_file_endpoint` rather than their own try/except.
- **Security headers:** backend `SecurityHeadersMiddleware` for `/api/*` and docs pages, `frontend/nginx.conf` for the SPA - change both. HSTS production-only.
- **Timestamps:** new models mix in `core/models/mixins.py`'s `TimestampMixin` (`created_at`/`updated_at`); domain times (`started_at`, `fetched_at`) keep their own names.
- **Lock files:** `backend/requirements.txt` / `requirements-dev.txt` are compiled with `uv pip compile` from their `.in`, never hand-edited (`docs/architecture/tooling.md`).

## Useful commands

`make help` lists every target (Docker lifecycle, `test`/`test-backend`/`test-frontend`, `lint*`, `migrate`, `sync-backend`) with the exact invocations CI uses - prefer them over hand-typed flags. `make test-backend`/`lint-backend` need a synced venv first (`make sync-backend`). Frontend dev server: `cd frontend && yarn start`. App at `http://localhost:4000`.
