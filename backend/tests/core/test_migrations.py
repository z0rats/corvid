"""Migration-chain smoke tests (docs/database-schema-audit.md, section 6, phase 0).

Two independent code paths can build the schema from scratch, and both need
to agree with `Base.metadata`:

1. `docker-entrypoint.py`: `alembic upgrade head` against a (possibly empty)
   database. The migration history is a single squashed revision that
   creates the schema exactly as `Base.metadata` declares it - there's no
   separate stamp-and-create_all path for a fresh install anymore (see that
   revision's docstring for why the old multi-migration history was
   squashed: nothing had shipped to a real installation yet).
2. `main.py`'s `_create_database_tables()` -> `Base.metadata.create_all()`,
   which still runs on every app startup regardless of how the schema got
   there. This is the actual bootstrap path for local dev without ever
   touching Alembic (e.g. `uvicorn main:app --reload` against a fresh
   `data/corvid.db`), so it's tested independently of the migration path.

Both tests run each step in its own subprocess: `app.core.database.engine` is a
module-level singleton built from `settings.database.url` at import time, so a
fresh interpreter per step (with `DB_URL` etc. set before Python starts) is the
only way to safely point it at a throwaway database without leaking into other
tests or the real `data/corvid.db`.
"""
import json
import os
import sqlite3
import subprocess
import sys
from pathlib import Path

import pytest

BACKEND_DIR = Path(__file__).resolve().parents[2]


def _env(tmp_path: Path) -> dict:
    """Environment for a subprocess pointed at an isolated, throwaway database.

    Overrides DATA_DIR/LOG_DIR too so `ensure_required_directories()` and the
    auto-generated encryption key don't touch the real `backend/data`.
    """
    env = os.environ.copy()
    env["DB_URL"] = f"sqlite:///{tmp_path / 'test.db'}"
    env["DATA_DIR"] = str(tmp_path / "data")
    env["LOG_DIR"] = str(tmp_path / "logs")
    return env


def _run(args: list[str], env: dict) -> subprocess.CompletedProcess:
    result = subprocess.run(
        args, cwd=BACKEND_DIR, env=env, capture_output=True, text=True, timeout=120,
    )
    if result.returncode != 0:
        pytest.fail(
            f"{' '.join(args)} exited {result.returncode}\n"
            f"--- stdout ---\n{result.stdout}\n--- stderr ---\n{result.stderr}"
        )
    return result


def _alembic(args: list[str], env: dict) -> subprocess.CompletedProcess:
    return _run([sys.executable, "-m", "alembic", *args], env)


def _create_all_tables(env: dict) -> None:
    _run(
        [sys.executable, "-c", "import asyncio\nfrom main import _create_database_tables\nasyncio.run(_create_database_tables())"],
        env,
    )


def _expected_table_names(env: dict) -> set[str]:
    """The full set of tables current models declare, independent of migration history.

    Importing `main` triggers `register_all_routers()` -> every router -> every
    CRUD module -> every model, the same transitive-import path that populates
    `Base.metadata` on a real app boot (see `_create_database_tables`'s own
    13-of-27 explicit import list, which relies on this same side effect).
    """
    result = _run(
        [sys.executable, "-c", "import json\nimport main\nfrom app.core.database import Base\nprint(json.dumps(sorted(Base.metadata.tables.keys())))"],
        env,
    )
    return set(json.loads(result.stdout.strip().splitlines()[-1]))


def _actual_table_names(tmp_path: Path) -> set[str]:
    con = sqlite3.connect(tmp_path / "test.db")
    try:
        rows = con.execute(
            "SELECT name FROM sqlite_master WHERE type='table' "
            "AND name NOT LIKE 'sqlite_%' AND name != 'alembic_version'"
        ).fetchall()
    finally:
        con.close()
    return {row[0] for row in rows}


def _head_revision(env: dict) -> str:
    result = _alembic(["heads"], env)
    return result.stdout.strip().split()[0]


def _stamped_revision(tmp_path: Path) -> str:
    con = sqlite3.connect(tmp_path / "test.db")
    try:
        row = con.execute("SELECT version_num FROM alembic_version").fetchone()
    finally:
        con.close()
    return row[0] if row else None


def test_fresh_install_alembic_upgrade_head_matches_current_models(tmp_path):
    """Empty DB -> `alembic upgrade head` alone, exactly like `docker-entrypoint.py`
    does for a brand-new volume, should produce every table current models declare."""
    env = _env(tmp_path)
    (tmp_path / "data").mkdir()
    (tmp_path / "logs").mkdir()

    _alembic(["upgrade", "head"], env)

    assert _actual_table_names(tmp_path) == _expected_table_names(env)
    assert _stamped_revision(tmp_path) == _head_revision(env)


def test_create_all_matches_current_models(tmp_path):
    """Empty DB -> `Base.metadata.create_all()` alone (no Alembic involved at all),
    exactly like `main.py` does on every startup, should also produce every table
    current models declare - this is the actual bootstrap path for local dev that
    never runs `alembic upgrade head`."""
    env = _env(tmp_path)
    (tmp_path / "data").mkdir()
    (tmp_path / "logs").mkdir()

    _create_all_tables(env)

    assert _actual_table_names(tmp_path) == _expected_table_names(env)


def test_migration_chain_downgrade_upgrade_round_trip(tmp_path):
    """Build a real (non-empty) database at head, then drive `downgrade()` back
    to base and `upgrade()` forward to head again.

    This is the regression test that protects future migrations added on top
    of the squashed initial-schema revision: any new migration must keep the
    *entire* chain replayable end to end, not just apply cleanly in isolation
    on whoever's machine authored it.
    """
    env = _env(tmp_path)
    (tmp_path / "data").mkdir()
    (tmp_path / "logs").mkdir()

    _alembic(["upgrade", "head"], env)
    expected = _expected_table_names(env)
    assert _actual_table_names(tmp_path) == expected  # sanity check before mutating further

    _alembic(["downgrade", "base"], env)
    _alembic(["upgrade", "head"], env)

    assert _actual_table_names(tmp_path) == expected
    assert _stamped_revision(tmp_path) == _head_revision(env)
