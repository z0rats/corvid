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

Settings are grouped by domain with their own prefix (`DB_`, `LOG_`, `API_`, `SCHEDULER_`, ...) —
see `backend/app/core/config/settings.py`.

## API keys

Per-service API keys (VirusTotal, Shodan, Hunter.io, etc.) are configured from the app itself
under **Settings → API Keys**, not via `.env`. Keys are encrypted at rest before being stored in
the database. See [Settings Reference](/corvid/getting-started/settings-reference/) for every
other settings tab.

## Backup

See [Backup & Operational Security](/corvid/getting-started/backup-and-operations/) for what
lives under `data/`, how to back it up safely, and disk-usage expectations.
