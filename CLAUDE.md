# OSINT Toolkit — project context

Self-hostable, single-user OSINT/security-analyst web app. FastAPI backend + React frontend, runs via Docker Compose. Not production-hardened (early prototype, per README).

## Stack

- **Backend**: Python 3.14, FastAPI, SQLAlchemy 2.0 (async, `aiosqlite`/`asyncpg`), Alembic migrations, APScheduler for background jobs, `pydantic-ai` for LLM features (Anthropic/OpenAI/Google/Groq/Mistral/xAI/Cohere/Bedrock all wired via `pydantic-ai-slim` extras), `slowapi` for rate limiting, pytest for tests.
- **Frontend**: React 19, MUI 9, Jotai (state), react-router-dom 7, react-scripts 5 (CRA, `--openssl-legacy-provider`), Yarn 4 (berry, `packageManager: yarn@4.15.0`).
- **DB**: SQLite by default at `data/osint_toolkit.db` (see `backend/app/core/config/settings.py` — `DatabaseSettings`, env prefix `DB_`). Logs at `data/logs/`.
- **Deploy**: `docker-compose.yaml` — `backend` (no exposed port, mounts `./data`) + `frontend` (nginx, port 4000). `make up` / `make rebuild` / `make up-backend` / `make up-frontend` (see `Makefile`).

## Backend architecture

Entry point: `backend/main.py` — builds the FastAPI app via `create_fastapi_application()`, lifespan hooks create DB tables, run app defaults, start background favicon fetch, start scheduler.

Layout under `backend/app/`:
- `core/` — cross-cutting: `config/` (settings, CORS, security headers, rate limiting, request-id, body-limit middleware), `settings/` (persisted app settings: `api_keys`, `ai_settings`, `general`, `keywords`, `modules`, `cti_profile` — each has its own models/schemas/crud/routers under `core/settings/<name>/`), `alerts/` (WebSocket alerts), `database.py`, `scheduler.py`, `dependencies.py`, `exceptions.py`, `healthcheck.py`.
- `features/` — one directory per product feature, each typically split into `routers/`, `service/`, `schemas/`, `models/`, `crud/`, `utils/`, `config/`:
  - `newsfeed/` — RSS aggregation, IOC extraction from articles, MITRE ATT&CK mapping, trends/analytics.
  - `ioc_tools/` — `ioc_lookup` (single + bulk lookups against AbuseIPDB, AlienVault, VirusTotal, Shodan, etc.), `ioc_extractor`, `ioc_defanger`, `domain_finder` (URLScan.io-based typosquat/phishing domain discovery).
  - `email_analyzer/` — `.eml` parsing, header/IOC checks, AI-assisted analysis.
  - `image_tools/` — EXIF/metadata extraction, hashing, reverse image search deep-links (no API key needed).
  - `llm_templates/` — user-defined AI prompt templates (categories + templates).
  - `cvss_calculator/` — CVSS 3.1/4.0 scoring.
- All routers are aggregated in `backend/app/utils/router_registry.py` via `get_core_routers()`, `get_settings_routers()`, `get_feature_routers()`, then mounted in `main.py`.
- Migrations: Alembic, config at `backend/alembic.ini`, scripts in `backend/migrations/versions/`. Run after schema changes: `docker compose run --rm backend alembic upgrade head`.
- Tests: `backend/tests/`, run with pytest (`pytest.ini` sets `testpaths = tests`, `pythonpath = .`). Currently sparse coverage (only `tests/features/image_tools`).

## Frontend architecture

`frontend/src/features/` mirrors the backend feature split — one directory per module (`newsfeed`, `ioc-tools`, `email-analyzer`, `image-tools`, `llm-templates`, `cvss-calculator`, `rule-creator` (Sigma/Yara/Snort rule builder), `settings`). Each feature dir typically has its own `components/`, `hooks/`, `services/` (API calls), `constants/`, `utils/`. Entry: `src/App.js` → `src/index.js`. `src/core/` holds shared/cross-feature code.

## Integrated external services

IOC/threat-intel lookups across IPs, domains, URLs, emails, hashes, CVEs via: AbuseIPDB, AlienVault OTX, CheckPhish, CrowdSec, GitHub, Google Safe Browsing, HIBP, Hunter.io, IPQualityScore, Maltiverse, NIST NVD, Pulsedive, Reddit, Shodan, ThreatFox, Twitter/X, URLScan.io, VirusTotal. API keys configured per-service in app settings (`core/settings/api_keys/`), not via `.env` for these.

## Conventions worth knowing

- Settings/config uses `pydantic-settings` with per-domain `BaseSettings` subclasses, each with its own `env_prefix` (e.g. `DB_`, `LOG_`, `API_`, `SCHEDULER_`), all loaded from a single `.env` (gitignored, not present in repo — none committed).
- In route handlers, prefer injecting settings via dependency (`SettingsDep`) rather than importing the module-level `settings` singleton, so tests can override via `app.dependency_overrides`.
- Feature module layering pattern: `routers` (HTTP) → `service` (business logic) → `crud` (DB access) → `models`/`schemas`. New features should follow this same split.
- AGPL-3.0 licensed (versions ≤ v0.1.0 are MIT). Be mindful of this when adding dependencies or discussing licensing.

## Useful commands

- `make up` / `make rebuild` — start (or rebuild + start) full stack via Docker.
- `make up-backend` / `make rebuild-backend`, `make up-frontend` / `make rebuild-frontend` — per-service.
- `docker compose run --rm backend alembic upgrade head` — apply DB migrations.
- Backend tests: `cd backend && pytest`.
- Frontend dev: `cd frontend && yarn start` (uses `--openssl-legacy-provider`); build: `yarn build`; test: `yarn test`.
- App served at `http://localhost:4000` once containers are up.
