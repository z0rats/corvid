---
title: Troubleshooting
description: Common issues and how to work around them.
---

## Lost the access token

If you didn't set a fixed `API_ACCESS_TOKEN` in `.env`, the token was auto-generated and saved to
`data/.access_token`. Retrieve it with `cat data/.access_token`, or check the backend logs
(`docker compose logs backend`). To force a new one, delete that file and restart the backend
container — a fresh token is generated on next startup. If you did set `API_ACCESS_TOKEN`, that
value always wins; update `.env` instead.

## Lost `data/.encryption_key`

Stored API keys become unrecoverable — the database itself is fine, but there's no way to decrypt
what's already stored. Re-enter your API keys under **Settings → API Keys** after restarting; a
new encryption key is generated automatically.

## A migration failed and the backend won't start

By design — a failed Alembic migration aborts startup rather than running the app against a
stale schema. Check `docker compose logs backend` for the migration error. If you need to inspect
the schema state without starting the whole app, run
`docker compose run --rm backend alembic upgrade head` manually and read its output directly.

## Email Search's SMTP checks always fail

Outbound TCP/25 is blocked by most cloud providers and Docker network setups by default, and
Gmail/Yandex/mail.de checkers rely on it. Enable `use_tor` or set a `proxy_url` in
[Email Search settings](/corvid/features/email-search/) if you need those checkers to work from
a restricted network. Alternatively, leave `enable_smtp_checks` off (the default) and rely on the
other checker groups.

## Email Search's headless-browser checks are slow or fail on first run

The Fastmail/int.pl/onet.pl checkers lazily download a Chromium binary
(~150-300 MB) the first time any of them actually runs — a slow or flaky network can make that
first scan time out. Subsequent scans reuse the already-downloaded binary and are much faster.

## Domain Finder / Dork Runner return few or no results from Google or Bing

Expected — DuckDuckGo's HTML endpoint is the default engine because Google and Bing block
scripted queries almost immediately. Google/Bing remain selectable as best-effort alternatives,
not a guaranteed path.

## Git Recon's clone-based scan times out or gets cut off

`url`/`nickname` mode clones full (non-shallow) repository history, which can take a while for
large repos/orgs. The scan runs up to `WALL_CLOCK_TIMEOUT_SECONDS` server-side, and nginx's
`/api/` proxy timeout is raised to match — if you've customized the reverse-proxy setup in front
of Corvid yourself, make sure its read timeout is at least as long.

## Disk space warnings

`GET /api/healthcheck/detailed` reports `"status": "low"` on the `disk` field once free space on
the `data/` mount drops below the configured threshold (1 GB by default). See
[Backup & Operational Security → Disk usage](/corvid/getting-started/backup-and-operations/#disk-usage)
for what typically consumes space over time.
