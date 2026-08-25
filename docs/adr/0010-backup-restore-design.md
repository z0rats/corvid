# In-app backup/restore: SQLite-only, restart-required, optional passphrase

The app previously had no in-app way to back up "all settings and history" — only the
operator-driven instructions in `backup-and-operations.md` (copy the whole `data/` dir) and the
incidental, non-user-facing pre-migration snapshots `docker-entrypoint.py` takes before running
`alembic upgrade head`. `core/backup/` (`service.py`/`routers.py`, mounted under
`/api/backup/*`) adds an on-demand export/import feature, with three scope decisions worth
recording.

## SQLite only

Postgres is already treated as unsupported everywhere else in this codebase
([0004](0004-sqlite-only-postgres-unsupported.md)) — no test runs against it, no doc lists it as
a deployment option. Building a second dump/restore mechanism (`pg_dump`/`pg_restore`) for a path
nothing else in the app exercises would be exactly the kind of feature CLAUDE.md's complexity
budget warns against. `get_backup_status`/`export_backup`/`restore_backup` all check
`engine.dialect.name` up front and return a 501 (`BACKUP_UNSUPPORTED_DIALECT`) pointing at the
database's own tooling for anything else.

## Archive contents and format

`corvid.db` (via SQLite's `VACUUM INTO`, not a raw file copy) + `.encryption_key` + optionally
`.access_token`, tarred and gzipped, with a `manifest.json` (app version, dialect, the DB's
stamped Alembic revision, creation time). `VACUUM INTO` produces a plain, consistent,
standalone snapshot with no separate `-wal`/`-shm` sidecars needed — a real advantage over
`docker-entrypoint.py`'s pre-migration backup, which has to grab those because it's a raw file
copy taken before the app (and this code) is even running.

Deliberately excluded: `data/logs/`, maigret's site database, pyppeteer's Chromium download —
none of those are "settings and history", they're logs/caches, and including them would bloat
every backup for no restorable benefit.

The access token is opt-in and off by default: it's usually already known to the operator
separately, and bundling it by default would put another sensitive item in every archive whether
or not the operator wants exact-token reproduction on restore. A passphrase is also opt-in: if
given, the whole archive is wrapped with a Fernet key derived via PBKDF2-HMAC-SHA256 (both
already dependencies via `cryptography`, so this needed nothing new). This backup is more
sensitive than anything else the app lets an operator export — it bundles the encryption key
*and* the ciphertext it unlocks — so passphrase protection is offered, but not forced on a
single-user local deployment that may not need it.

## Restore is restart-required, not an in-process hot-swap

A restore could try to hot-swap the live `AsyncEngine` mid-process (dispose it, swap files, run
`alembic upgrade head` via Alembic's Python API, recreate the engine) for a seamless
no-restart experience. That's a lot of moving parts touching shared engine/connection-pool state
for a codebase that's an early prototype, not production-hardened, and CLAUDE.md already asks for
extra scrutiny on any change to shared/concurrent state.

Instead, `restore_backup` validates the archive (manifest dialect match, a recognized Alembic
revision, `PRAGMA integrity_check` on the extracted DB), then does the whole file swap with
`os.replace` — an atomic rename. Already-open file descriptors (the running process's connection
pool) keep pointing at the pre-restore file's inode and keep working exactly as before; only a
process that opens the path *after* the swap sees the restored file. That's what makes
"just tell the operator to restart the backend" both correct and safe with zero engine-lifecycle
code: restarting re-runs the exact same `docker-entrypoint.py` startup sequence
(chown → `alembic upgrade head` → exec) that already handles a normal deploy, now pointed at the
restored `corvid.db`.

The tradeoff is UX, not safety: the response says `restart_required: true`, and the operator has
to restart the container themselves. If a future version of this app moves toward less
manual operation, an in-process hot-swap is the natural next step — but it should be its own
change, with its own tests around engine disposal/recreation under concurrent request load, not
bundled into this one.
