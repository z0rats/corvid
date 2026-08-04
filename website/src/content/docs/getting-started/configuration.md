---
title: Configuration
description: Environment variables, API keys, and backup.
---

## Environment variables

Copy [`.env.example`](https://github.com/z0rats/corvid/blob/main/.env.example) to `.env` at the
repo root to override any setting — all of them have working defaults, so this step is optional.
`.env` is read automatically by `docker compose up` (via `env_file` on the `backend` service).

Settings are grouped by domain with their own prefix (`DB_`, `LOG_`, `API_`, `SCHEDULER_`, ...) —
see `backend/app/core/config/settings.py`.

## API keys

Per-service API keys (VirusTotal, Shodan, Hunter.io, etc.) are configured from the app itself
under **Settings → API Keys**, not via `.env`. Keys are encrypted at rest before being stored in
the database.

## Backup

Everything Corvid needs to keep running lives under the host-mounted `data/` directory:

- `data/corvid.db` — SQLite database: investigation history, settings, and encrypted API keys.
- `data/.encryption_key` — decrypts the API keys stored in the database. Losing this file makes
  stored keys unrecoverable even though the database itself is intact.
- `data/.access_token` — the bearer token protecting the app. Losing it isn't a data-loss risk —
  a new one is generated on next startup.
- `data/logs/` — optional, rotated application logs.

Back up `data/` as a whole (stop the container first for a consistent SQLite snapshot, or use
`sqlite3 .backup` for a live one), preserving file permissions in transit
(`tar --preserve-permissions`, `rsync -a`) — a backup method that doesn't preserve modes/ownership
defeats the encryption-at-rest story for `.encryption_key` and `.access_token`.
