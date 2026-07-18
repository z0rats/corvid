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
migration aborts startup instead of serving against a stale schema.

A brand-new, empty database is stamped to head instead of migrated: alembic's
oldest migration assumes the base schema already exists (true historically,
since it was created via the app's own `Base.metadata.create_all()` before
alembic was introduced), so replaying it against zero tables fails. Stamping
is metadata-only (writes `alembic_version`, runs no DDL) and lets the app's
own startup build the current schema exactly as it always has on a first run.
"""
import asyncio
import os
import pwd
import subprocess
import sys

APP_USER = "appuser"
DATA_DIR = "/backend/data"


def _database_is_empty() -> bool:
    """True if the target database has no tables yet (fresh install/volume)."""
    from sqlalchemy import inspect
    from app.core.database import engine

    async def _check() -> bool:
        async with engine.connect() as conn:
            names = await conn.run_sync(lambda sync_conn: inspect(sync_conn).get_table_names())
            return len(names) == 0

    return asyncio.run(_check())


def _run_migrations() -> None:
    is_empty = _database_is_empty()
    command = ["alembic", "stamp", "head"] if is_empty else ["alembic", "upgrade", "head"]
    label = "Stamping fresh database at migration head" if is_empty else "Running database migrations (alembic upgrade head)"
    print(f"{label}...", flush=True)
    result = subprocess.run(command, cwd="/backend")
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

    _run_migrations()

    os.execvp(sys.argv[1], sys.argv[1:])


if __name__ == "__main__":
    main()
