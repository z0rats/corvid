---
title: Backup & Operational Security
description: Backing up data/, disk usage, and safe operating practices.
sidebar:
  order: 50
---

## Backup

Everything Corvid needs to keep running lives under the host-mounted `data/` directory:

- `data/corvid.db` — SQLite database: investigation history, settings, and encrypted API keys.
- `data/.encryption_key` — decrypts the API keys stored in the database. Losing this file makes
  stored keys unrecoverable even though the database itself is intact; re-entering the keys is
  the only fix.
- `data/.access_token` — the bearer token protecting the app. Losing it isn't a data-loss risk —
  a new one is generated on next startup and you just re-enter it in the browser.
- `data/logs/` — optional, rotated application logs.

Losing `data/` entirely means starting over from a blank instance; there is no other durable
state.

### In-app backup/restore

Settings → Backup lets you download a full backup (the database, produced via a consistent
`VACUUM INTO` snapshot, plus the encryption key) and restore from a previously downloaded one,
without leaving the browser. The access token is left out of the archive by default — check
"Include the access token" if you specifically want a restore to reproduce the exact same token.
Optionally set a passphrase to encrypt the archive (PBKDF2-derived key, no new dependency) before
it's stored anywhere; there's no way to recover a lost passphrase, so keep it somewhere durable if
you set one.

This only supports the default SQLite backend — a non-SQLite deployment
(see [SQLite is the only supported backend](https://github.com/z0rats/corvid/blob/main/docs/adr/0004-sqlite-only-postgres-unsupported.md))
gets a 501 from `/api/backup/*` and should use its own database's dump/restore tooling instead.

**Restoring requires a manual restart.** The restore endpoint validates and writes the new
database/key/token files to disk, but the currently running backend process keeps serving the
pre-restore data until you restart it (`docker compose restart backend`, or `make rebuild`) — that
restart is what runs the normal startup migration check against the restored database, the same
as any other deploy.

### Manual backup

The in-app flow above covers day-to-day use; for a full host-level snapshot, or if you're not on
SQLite, back up `data/` as a whole instead — stop the container first for a consistent SQLite
snapshot, or use `sqlite3 .backup` for a live one.

**Permissions travel with the backup.** `.encryption_key` and `.access_token` are written `0600`
on the host, but that only protects them *in place*. A backup method that doesn't preserve file
modes/ownership (a permissive `tar` extraction, copying into a world-readable cloud-sync folder,
`chmod -R` during restore) — or that lands the backup somewhere with broader access than the
source host — defeats the encryption-at-rest story: the key ends up sitting right next to the
ciphertext it decrypts. Preserve permissions in transit (`tar --preserve-permissions`, `rsync -a`)
and restrict access to the backup destination at least as tightly as `data/` itself.

## Disk usage

`data/` has no total-size guard, so keep an eye on the host mount over time. Rough steady-state
contributors: the SQLite database and rotated logs stay small (tens of MB); Maigret's site
database and its own image-hash cache add tens of MB; `email_search`'s headless checkers (if
enabled) lazily download a Chromium binary the first time they run (~150-300 MB, plus its own
runtime footprint); exported reports accumulate if you generate a lot of them and never clean up.

The backend logs a warning at startup — and `GET /api/healthcheck/detailed`'s `disk` field reports
`"status": "low"` — once free space on the `data/` mount drops below 1 GB (configurable via
`LOW_DISK_SPACE_THRESHOLD_BYTES`), but nothing actively stops writes past that point; treat it as
an early signal, not a hard limit.

## Operational security notes

This tool talks to third-party services (VirusTotal, Shodan, target mail servers via
`email_search`'s SMTP checks, etc.) using your own infrastructure's IP, and stores investigation
history in a local database. Some practices worth following, especially for sensitive
engagements:

- **Isolate the instance.** Run it on a dedicated VM/VPS or an isolated host, not your
  daily-driver machine — a target under investigation can potentially see inbound lookups
  against them.
- **Route sensitive lookups through Tor/a proxy.** `email_search` supports `use_tor`/`proxy_url`,
  and Username Search's Maigret source has its own proxy setting, for when a target could
  plausibly monitor who's probing them.
- **Never enable `SECURITY_ALLOW_PRIVATE_NETWORK_TARGETS` outside dev/testing** — it's a direct
  SSRF opt-out (see [Security](/corvid/architecture/security/)).
- **Segment and rotate API keys** per engagement where the provider supports multiple keys, so a
  compromised key from one case doesn't expose others.
- **Don't cross-contaminate identities.** Some features (e.g. Image Tools' reverse-search
  deep-links) open external services directly in your browser — use a separate, logged-out
  browser profile for sensitive lookups so they don't tie back to your personal accounts.
