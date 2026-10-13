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
| `ENVIRONMENT` | `development` | Set to `production` to enable HSTS (only behind HTTPS). |
| `STATIC_DIR` | `app/static` | Static files directory (holds cached newsfeed feed icons). |
| `DATA_DIR` | `data` | Where the database, logs, access token, and encryption key live. |
| `LOW_DISK_SPACE_THRESHOLD_BYTES` | `1073741824` | Free space on the `data/` mount below which the health check reports "low" disk status. |
| `DB_URL` | `sqlite:///./data/corvid.db` | Database URL. Only SQLite is supported. |
| `DB_ECHO`, `DB_POOL_SIZE`, `DB_MAX_OVERFLOW`, `DB_POOL_RECYCLE` | `false`, `10`, `20`, `3600` | SQLAlchemy engine tuning. |
| `LOG_LEVEL`, `LOG_DIR`, `LOG_APP_NAME`, `LOG_MAX_FILE_SIZE`, `LOG_BACKUP_COUNT`, `LOG_ENABLE_CONSOLE`, `LOG_ENABLE_FILE` | `INFO`, `data/logs`, `corvid`, 10 MiB, `5`, `true`, `true` | Logging level, location, rotation, and which handlers are on. API-key-shaped strings are redacted from all of them. |
| `API_TITLE`, `API_DESCRIPTION`, `API_DEBUG`, `API_VERSION` | `Corvid`, built-in text, `false`, auto | API metadata shown on `/docs`. `API_VERSION` is stamped by the release image; leave it unset. |
| `API_MAX_REQUEST_BODY_BYTES` | `52428800` | Maximum request body size (50 MiB), which also bounds uploads. |
| `API_CORS_ORIGINS`, `API_TRUSTED_HOSTS` | `["http://localhost:3000"]`, `["localhost","127.0.0.1"]` | JSON arrays; only change them if you're not using the default nginx setup on `:4000`. |
| `API_ACCESS_TOKEN` | auto-generated | The shared bearer token. Empty generates one on first start and persists it to `<DATA_DIR>/.access_token`. Setting it pins the value and disables regeneration from **Settings → About**. |
| `SECURITY_ALLOW_PRIVATE_NETWORK_TARGETS` | `false` | Dev/testing only: lets SSRF-guarded requests reach private, loopback, and link-local addresses. Never enable on a reachable instance. |
| `SECURITY_ENCRYPTION_KEY` | auto-generated | Encrypts API keys at rest. Empty generates one and persists it to `<DATA_DIR>/.encryption_key`; back it up with the database, since losing it makes stored keys unrecoverable. |
| `SCHEDULER_DEFAULT_FETCH_INTERVAL` | `30` | Default newsfeed fetch interval, in minutes. |
| `SCHEDULER_MAX_JOB_INSTANCES` | `1` | Concurrent instances allowed per scheduled job. |
| `SCHEDULER_BLACKLIST_REFRESH_INTERVAL_HOURS` | `24` | How often the crypto-address blacklist is refreshed. |
| `LLM_OLLAMA_BASE_URL` | `http://localhost:11434/v1` | A local Ollama server's OpenAI-compatible API; models pulled there are auto-discovered in **AI Settings**. In Docker on macOS/Windows use `host.docker.internal` instead of `localhost`. |

## API keys

Per-service API keys (VirusTotal, Shodan, Hunter.io, etc.) are configured from the app itself
under **Settings → API Keys**, not via `.env`. Keys are encrypted at rest before being stored in
the database. See [Settings Reference](/corvid/getting-started/settings-reference/) for every
other settings tab.

## Backup

See [Backup & Operational Security](/corvid/getting-started/backup-and-operations/) for what
lives under `data/`, how to back it up safely, and disk-usage expectations.
