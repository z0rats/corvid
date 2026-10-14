"""Migration-chain smoke tests.

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
        args,
        cwd=BACKEND_DIR,
        env=env,
        capture_output=True,
        text=True,
        timeout=120,
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
        [
            sys.executable,
            "-c",
            (
                "import asyncio\nfrom main import "
                "_create_database_tables\nasyncio.run(_create_database_tables())"
            ),
        ],
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
        [
            sys.executable,
            "-c",
            (
                "import json\nimport main\nfrom app.core.database import "
                "Base\nprint(json.dumps(sorted(Base.metadata.tables.keys())))"
            ),
        ],
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


def test_reliability_migration_keeps_existing_articles(tmp_path):
    """`a7c41e90b3d2` adds a column to `newsfeed_settings`, the parent of
    `news_articles` (`ON DELETE CASCADE`). A table-recreating (batch) migration would,
    with the app's `PRAGMA foreign_keys=ON`, silently delete every stored article on
    upgrade - so seed one and check it survives both directions."""
    env = _env(tmp_path)
    (tmp_path / "data").mkdir()
    (tmp_path / "logs").mkdir()

    _alembic(["upgrade", "43f3a99819ae"], env)
    con = sqlite3.connect(tmp_path / "test.db")
    try:
        con.execute(
            "INSERT INTO newsfeed_settings(name, url, icon, icon_id, enabled, deleted) "
            "VALUES ('f', 'https://x.test/rss', 'default.png', 'i', 1, 0)"
        )
        con.execute(
            "INSERT INTO news_articles(feedname, icon, title, summary, date, link, "
            "fetched_at, tlp, read) VALUES ('f', 'default.png', 't', 's', '2026-01-01', "
            "'https://x.test/1', '2026-01-01', 'TLP:CLEAR', 0)"
        )
        con.commit()
    finally:
        con.close()

    def article_count() -> int:
        con = sqlite3.connect(tmp_path / "test.db")
        try:
            return con.execute("SELECT count(*) FROM news_articles").fetchone()[0]
        finally:
            con.close()

    _alembic(["upgrade", "head"], env)
    assert article_count() == 1

    _alembic(["downgrade", "43f3a99819ae"], env)
    assert article_count() == 1


def test_mail_search_source_migration_keeps_existing_runs_and_results(tmp_path):
    """`b3d90f1a7c55` adds `mail_searches.source`; `mail_search_results` cascades from it, so a
    table-recreating (batch) migration would delete every stored result under the app's
    `PRAGMA foreign_keys=ON`. Existing rows must also come out as `mailcat` runs."""
    env = _env(tmp_path)
    (tmp_path / "data").mkdir()
    (tmp_path / "logs").mkdir()

    _alembic(["upgrade", "a7c41e90b3d2"], env)
    con = sqlite3.connect(tmp_path / "test.db")
    try:
        con.execute(
            "INSERT INTO mail_searches(id, username, status, total_providers_checked, found_count, "
            "started_at) VALUES (1, 'alice', 'completed', 26, 1, '2026-01-01')"
        )
        con.execute(
            "INSERT INTO mail_search_results(search_id, provider_name, emails) "
            "VALUES (1, 'gmail', '[\"alice@gmail.com\"]')"
        )
        con.commit()
    finally:
        con.close()

    def read() -> tuple[int, list]:
        con = sqlite3.connect(tmp_path / "test.db")
        try:
            results = con.execute("SELECT count(*) FROM mail_search_results").fetchone()[0]
            cols = {r[1] for r in con.execute("PRAGMA table_info(mail_searches)")}
            sources = (
                [r[0] for r in con.execute("SELECT source FROM mail_searches")]
                if "source" in cols
                else []
            )
            return results, sources
        finally:
            con.close()

    _alembic(["upgrade", "head"], env)
    assert read() == (1, ["mailcat"])

    _alembic(["downgrade", "a7c41e90b3d2"], env)
    assert read() == (1, [])


def test_maigret_parent_migration_keeps_existing_runs_and_results(tmp_path):
    """`c5e18a3d9f20` adds columns to `maigret_searches`; `maigret_site_results` cascades from
    it, so a table-recreating (batch) migration would delete every stored result under the app's
    `PRAGMA foreign_keys=ON`."""
    env = _env(tmp_path)
    (tmp_path / "data").mkdir()
    (tmp_path / "logs").mkdir()

    _alembic(["upgrade", "b3d90f1a7c55"], env)
    con = sqlite3.connect(tmp_path / "test.db")
    try:
        con.execute(
            "INSERT INTO maigret_searches(id, username, source, status, total_sites_checked, "
            "found_count, started_at) VALUES (1, 'alice', 'maigret', 'completed', 500, 1, "
            "'2026-01-01')"
        )
        con.execute(
            "INSERT INTO maigret_site_results(search_id, site_name, url_user) "
            "VALUES (1, 'GitHub', 'https://github.com/alice')"
        )
        con.commit()
    finally:
        con.close()

    def read() -> tuple[int, set[str]]:
        con = sqlite3.connect(tmp_path / "test.db")
        try:
            results = con.execute("SELECT count(*) FROM maigret_site_results").fetchone()[0]
            cols = {r[1] for r in con.execute("PRAGMA table_info(maigret_searches)")}
            return results, cols & {"parent_search_id", "pivot_source"}
        finally:
            con.close()

    _alembic(["upgrade", "head"], env)
    assert read() == (1, {"parent_search_id", "pivot_source"})

    _alembic(["downgrade", "b3d90f1a7c55"], env)
    assert read() == (1, set())


@pytest.mark.parametrize(("before", "after"), [(0, 30), (7, 7), (365, 365)])
def test_newsfeed_retention_migration_moves_only_unlimited_to_30_days(tmp_path, before, after):
    """`e4b7a2c91d06` makes 30 days the article-retention default: the old default 0
    ("unlimited", which never actually pruned anything) moves to 30, while a deliberately
    chosen finite period is left alone."""
    env = _env(tmp_path)
    (tmp_path / "data").mkdir()
    (tmp_path / "logs").mkdir()

    _alembic(["upgrade", "c5e18a3d9f20"], env)
    con = sqlite3.connect(tmp_path / "test.db")
    try:
        con.execute(
            "INSERT INTO newsfeed_config(id, retention_days, background_fetch_enabled, "
            "fetch_interval_minutes, keyword_matching_enabled) VALUES (1, ?, 1, 60, 0)",
            (before,),
        )
        con.commit()
    finally:
        con.close()

    _alembic(["upgrade", "head"], env)

    con = sqlite3.connect(tmp_path / "test.db")
    try:
        assert con.execute("SELECT retention_days FROM newsfeed_config").fetchone()[0] == after
    finally:
        con.close()
