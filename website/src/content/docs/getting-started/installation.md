---
title: Installation
description: Deploy Corvid with Docker Compose.
---

## System requirements

- Docker Engine 24+ with the Docker Compose v2 plugin (`docker compose`, not the legacy
  standalone `docker-compose` binary)
- Linux, macOS, or Windows (via Docker Desktop/WSL2)
- ~1 GB free disk for the app itself; more if you enable `email_search`'s optional headless
  checkers, which lazily download a Chromium binary (~150-300 MB) on first use
- Outbound HTTPS access for the third-party services you configure (VirusTotal, Shodan, etc.) —
  no inbound ports need to be exposed
- No GPU required. As a single-user tool with no background crawling by default, a small VM
  (1-2 vCPU, 2 GB RAM) is comfortable for typical use

## Option A — one-line install (pre-built images)

Pulls ready-made images from GHCR instead of building from source. Installs into `~/corvid` by
default (override with `CORVID_DIR`):

```bash
curl -fsSL https://raw.githubusercontent.com/z0rats/corvid/main/install.sh | bash
```

Once it's running, open http://localhost:4000. There's no auto-update — new versions aren't
pulled without your say-so. To update later, run `./update.sh` from the install directory.

## Option B — build from source

Gives you a local build instead of pulling from a registry, and lets you review the Dockerfiles
before anything runs:

1. Download the repository and extract the files.
2. Navigate to the directory where `docker-compose.yaml` is located.
3. Start the application:
   - `make up` — start backend and frontend without rebuilding
   - `make rebuild` — rebuild images (e.g. after dependency or Dockerfile changes) and start
   - `make up-backend` / `make up-frontend` — start a single service without rebuilding
   - `make rebuild-backend` / `make rebuild-frontend` — rebuild and start a single service
4. Open http://localhost:4000.

Database migrations run automatically on container startup — no manual step needed after
`make rebuild`.

## Access token

The app has no user accounts, so it's protected by a single access token instead of a login
form. On first startup, a token is generated automatically and printed to the backend logs
(`docker compose logs backend`) and saved to `data/.access_token` on the host. Open the app and
you'll be asked to paste that token once — it's then remembered in the browser.

To set your own fixed token instead of the auto-generated one, set `API_ACCESS_TOKEN` in `.env`
before starting the container.
