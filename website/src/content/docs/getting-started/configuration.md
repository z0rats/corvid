---
title: Configuration
description: Environment variables, API keys, and backup.
sidebar:
  order: 30
---

## Environment variables

Copy [`.env.example`](https://github.com/z0rats/corvid/blob/main/.env.example) to `.env` at the
repo root to override any setting — all of them have working defaults, so this step is optional.
`.env` is read automatically by `docker compose up` (via `env_file` on the `backend` service).

Settings are grouped by domain with their own prefix — see
`backend/app/core/config/settings.py`. Every variable below is optional.

| Variable | Default | What it does |
| --- | --- | --- |
| `FRONTEND_PORT` | `4000` | Host port the frontend is published on (Docker Compose only; the app doesn't read it). |
| `CORVID_VERSION` | `latest` | Image tag `docker-compose.prod.yaml` runs (one-line-installer deployments only), e.g. `2.4.0`. Set by `./update.sh [version]`; see [Updating and rolling back](/corvid/getting-started/installation/#updating-and-rolling-back). |
| `BACKEND_MEM_LIMIT` | `0` (no limit) | Hard memory cap for the backend container, e.g. `2g` (Docker Compose only). On a small VM it keeps a burst of heavy scans from exhausting the host's memory: Docker kills and restarts only the backend container instead. See also `SCAN_MAX_CONCURRENT_HEAVY`. |
| `ENVIRONMENT` | `development` | Set to `production` to enable HSTS (only behind HTTPS). |
| `STATIC_DIR` | `app/static` | Static files directory (holds cached newsfeed feed icons). |
| `DATA_DIR` | `data` | Where the database, logs, access token, and encryption key live. |
| `LOW_DISK_SPACE_THRESHOLD_BYTES` | `1073741824` | Free space on the `data/` mount below which the health check reports "low" disk status. |
| `DB_URL` | `sqlite:///./data/corvid.db` | Database URL. Only SQLite is supported. |
| `DB_ECHO`, `DB_POOL_SIZE`, `DB_MAX_OVERFLOW` | `false`, `10`, `20` | SQLAlchemy engine tuning. |
| `LOG_LEVEL`, `LOG_DIR`, `LOG_APP_NAME`, `LOG_MAX_FILE_SIZE`, `LOG_BACKUP_COUNT`, `LOG_ENABLE_CONSOLE`, `LOG_ENABLE_FILE` | `INFO`, `data/logs`, `corvid`, 10 MiB, `5`, `true`, `true` | Logging level, location, rotation, and which handlers are on. API-key-shaped strings are redacted from all of them. |
| `API_TITLE`, `API_DESCRIPTION`, `API_DEBUG`, `API_VERSION` | `Corvid`, built-in text, `false`, auto | API metadata shown on `/docs`. `API_VERSION` is stamped by the release image; leave it unset. |
| `API_MAX_REQUEST_BODY_BYTES` | `52428800` | Maximum request body size (50 MiB), which also bounds uploads. |
| `API_CORS_ORIGINS` | `["http://localhost:3000"]` | JSON array; only change it if you're not using the default nginx setup on `:4000`. |
| `API_TRUSTED_HOSTS` | `["*"]` | JSON array of accepted `Host` header values. The default accepts any, so the app works by LAN IP or hostname; the access token is what protects the API. Narrow it (e.g. `["corvid.lan"]`) to reject requests under any other name. |
| `API_ACCESS_TOKEN` | auto-generated | The shared bearer token. Empty generates one on first start and persists it to `<DATA_DIR>/.access_token`. Setting it pins the value and disables regeneration from **Settings → About**. |
| `SECURITY_ALLOW_PRIVATE_NETWORK_TARGETS` | `false` | Dev/testing only: lets SSRF-guarded requests reach private, loopback, and link-local addresses. Never enable on a reachable instance. |
| `SECURITY_ENCRYPTION_KEY` | auto-generated | Encrypts API keys at rest. Empty generates one and persists it to `<DATA_DIR>/.encryption_key`; back it up with the database, since losing it makes stored keys unrecoverable. |
| `SCHEDULER_DEFAULT_FETCH_INTERVAL` | `30` | Default newsfeed fetch interval, in minutes. |
| `SCHEDULER_MAX_JOB_INSTANCES` | `1` | Concurrent instances allowed per scheduled job. |
| `SCHEDULER_BLACKLIST_REFRESH_INTERVAL_HOURS` | `24` | How often the crypto-address blacklist is refreshed. |
| `SCAN_MAX_CONCURRENT_HEAVY` | `3` | Resource-heavy scans (Maigret, social-analyzer, user_scanner, Amass, Git Recon's clone modes) allowed to run at once. Further ones wait in a queue, shown as "queued" in the UI; lighter scans aren't limited. Lower it on a small VM.
| `LLM_OLLAMA_BASE_URL` | `http://localhost:11434/v1` | A local Ollama server's OpenAI-compatible API; models pulled there are auto-discovered in **AI Settings**. In Docker on macOS/Windows use `host.docker.internal` instead of `localhost`. |

## API keys

Per-service API keys (VirusTotal, Shodan, Hunter.io, etc.) are configured from the app itself
under **Settings → API Keys**, not via `.env`. Keys are encrypted at rest before being stored in
the database. See [Settings Reference](/corvid/getting-started/settings-reference/) for every
other settings tab.

## Backup

See [Backup & Operational Security](/corvid/getting-started/backup-and-operations/) for what
lives under `data/`, how to back it up safely, and disk-usage expectations.
