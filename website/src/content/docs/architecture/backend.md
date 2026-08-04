---
title: Backend
description: Backend stack and layout.
---

## Stack

- **Python 3.14**, **FastAPI**
- **SQLAlchemy 2.0** (async, `aiosqlite`/`asyncpg`) with **Alembic** migrations
- **APScheduler** for background jobs (feed polling, favicon fetching, etc.)
- **pydantic-ai-slim** for LLM features — Anthropic, Google, and OpenAI providers, plus
  auto-discovery of any model pulled into a local Ollama server
- **SQLite** by default at `data/corvid.db`

## Layout

```
backend/app/
├── core/       cross-cutting: config, settings, security, reports, scheduler
└── features/   one directory per product feature
```

Each feature under `features/` is typically split into `routers/` (HTTP), `service/` (business
logic), `crud/` (DB access), `models/`, and `schemas/` — a consistent layering pattern across the
whole backend.

## Access control

The app has no user accounts — it's a single-user tool. Every `/api/*` route is instead guarded
behind one shared bearer token, checked as a router-level dependency. The token is provided via
`API_ACCESS_TOKEN` or auto-generated and persisted on first startup.

## Migrations

Alembic migrations run automatically on container startup, before the app starts serving traffic
— a failed migration aborts startup rather than serving against a stale schema. The migration
history is a single squashed revision that creates the schema from scratch, so it applies the
same way to a brand-new database as to an existing one.

## Scan-style features

Long-running features (Username Search, Email Search, Git Recon) share the same lifecycle
mechanics rather than each reimplementing them: progress streams over Server-Sent Events, scans
are cancellable and resumable across a dropped connection, and a scan interrupted by a container
restart is reconciled to a `failed` state rather than staying stuck `running` forever.

## Testing

Backend tests live in `backend/tests/`, run with pytest, with coverage uploaded to Codecov on
every push. See [Security](/corvid/architecture/security/) for CI's dependency/image scanning and
[Local Development](/corvid/getting-started/local-development/) for running tests yourself.
