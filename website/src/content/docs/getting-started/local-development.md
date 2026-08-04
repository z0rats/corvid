---
title: Local Development
description: Running the backend, frontend, and docs site without Docker.
---

Docker Compose is the primary way to run Corvid (see [Installation](/corvid/getting-started/installation/)),
but each part can also run directly on the host for faster iteration.

## Backend

```bash
cd backend
uv pip install -r requirements.txt --override lxml-override.txt
pytest
```

Syncing with `--override lxml-override.txt` matters — `maigret` and `newspaper4k` pin
incompatible `lxml` ranges, resolved by that override file. A stale or partial local venv can
pass tests locally while missing an import error that a full install would catch, so re-sync
before trusting a green run.

Migrations run automatically against a fresh database via `Base.metadata.create_all()` on
startup outside Docker; to run Alembic migrations manually:

```bash
docker compose run --rm backend alembic upgrade head
```

## Frontend

```bash
cd frontend
yarn start   # dev server, uses --openssl-legacy-provider
yarn test    # Vitest
yarn lint    # ESLint
```

## Docs site

```bash
cd website
yarn dev     # Astro dev server
yarn build   # static build to website/dist/
```

## Full stack via Docker

- `make up` / `make rebuild` — start (or rebuild + start) the full stack.
- `make up-backend` / `make rebuild-backend`, `make up-frontend` / `make rebuild-frontend` —
  per-service.
