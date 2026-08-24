#!/usr/bin/env python3
"""Container entrypoint: chown the bind-mounted data dir, then drop from root
to the unprivileged app user before exec'ing the real command.

A plain Dockerfile `USER` directive isn't enough here: `/backend/data` is a
host bind mount (see docker-compose.yaml), so it keeps whatever ownership the
host directory already has, regardless of what the image sets at build time -
without this, the app user could get a permission error on first write.

Uses a plain setuid/setgid + execvp instead of gosu/su-exec so the image
doesn't need an extra installed tool; execvp performs a real execve, so the
final process still becomes PID 1 with correct signal handling.
Also runs `alembic upgrade head` (as `appuser`, after dropping privileges) before
exec'ing the real command, so a self-hoster who forgets the manual migration step
after `make rebuild` doesn't end up running against a stale schema. Single-operator
tool, so an unattended auto-migration is an acceptable tradeoff here; a failed
migration aborts startup instead of serving against a stale schema. Works the
same for a brand-new, empty database as for an existing one: the migration
history is a single squashed revision that creates the schema from scratch
(see `migrations/versions/`), so there's no separate stamp-and-create_all path
for a fresh install anymore.

Right before migrating, an existing SQLite database is copied into
`data/backups/<timestamp>/`. SQLite has no transactional DDL and
`migrations/env.py`'s `do_run_migrations` doesn't wrap a multi-step revision in
one batch, so a migration that fails partway through can otherwise leave the
schema stuck with no way back except a manually-restored copy. Only the last
few backups are kept.
"""

import os
import pwd
import shutil
import subprocess
import sys
from datetime import UTC, datetime

APP_USER = "appuser"
DATA_DIR = "/backend/data"
BACKUP_DIR = os.path.join(DATA_DIR, "backups")
BACKUPS_TO_KEEP = 5


def _sqlite_db_path() -> str | None:
    """Resolve the on-disk path for a `sqlite:///`-style DB_URL, or None for a
    non-SQLite backend (the only other case `DB_URL` is used for - see
    `docs/adr/0004-sqlite-only-postgres-unsupported.md` - and one this script
    has no business backing up)."""
    url = os.environ.get("DB_URL", "sqlite:///./data/corvid.db")
    if not url.startswith("sqlite:///"):
        return None
    path = url.removeprefix("sqlite:///")
    return path if os.path.isabs(path) else os.path.normpath(os.path.join("/backend", path))


def _prune_old_backups() -> None:
    if not os.path.isdir(BACKUP_DIR):
        return
    snapshots = sorted(
        d for d in os.listdir(BACKUP_DIR) if os.path.isdir(os.path.join(BACKUP_DIR, d))
    )
    for stale in snapshots[:-BACKUPS_TO_KEEP]:
        shutil.rmtree(os.path.join(BACKUP_DIR, stale))


def _backup_database() -> None:
    db_path = _sqlite_db_path()
    if db_path is None or not os.path.exists(db_path):
        return  # non-SQLite backend, or first run with no DB file yet

    timestamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%S.%fZ")
    dest_dir = os.path.join(BACKUP_DIR, timestamp)
    os.makedirs(dest_dir, exist_ok=True)
    for suffix in ("", "-wal", "-shm"):
        src = db_path + suffix
        if os.path.exists(src):
            shutil.copy2(src, os.path.join(dest_dir, os.path.basename(src)))
    print(f"Backed up database to {dest_dir} before migrating.", flush=True)

    _prune_old_backups()


def _run_migrations() -> None:
    print("Running database migrations (alembic upgrade head)...", flush=True)
    result = subprocess.run(["alembic", "upgrade", "head"], cwd="/backend")
    if result.returncode != 0:
        print("Database migration failed; aborting startup.", file=sys.stderr, flush=True)
        sys.exit(result.returncode)
    print("Database migrations applied successfully.", flush=True)


def main() -> None:
    os.makedirs(DATA_DIR, exist_ok=True)

    pw = pwd.getpwnam(APP_USER)
    for root, dirs, files in os.walk(DATA_DIR):
        os.chown(root, pw.pw_uid, pw.pw_gid)
        for name in dirs + files:
            os.chown(os.path.join(root, name), pw.pw_uid, pw.pw_gid)

    os.environ["HOME"] = pw.pw_dir
    os.initgroups(APP_USER, pw.pw_gid)
    os.setgid(pw.pw_gid)
    os.setuid(pw.pw_uid)

    _backup_database()
    _run_migrations()

    os.execvp(sys.argv[1], sys.argv[1:])


if __name__ == "__main__":
    main()
