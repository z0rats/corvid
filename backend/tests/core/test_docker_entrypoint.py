"""Tests for the pre-migration SQLite backup helpers in `docker-entrypoint.py`.

Loaded via `importlib` (not a plain import) since the module lives outside the
`app` package and its filename isn't a valid Python identifier.
"""

import importlib.util
import os
import sys
from pathlib import Path

import pytest

_SPEC = importlib.util.spec_from_file_location(
    "docker_entrypoint", Path(__file__).parents[2] / "docker-entrypoint.py"
)
entrypoint = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(entrypoint)


@pytest.fixture
def backup_dir(tmp_path, monkeypatch):
    dest = tmp_path / "backups"
    monkeypatch.setattr(entrypoint, "BACKUP_DIR", str(dest))
    return dest


def test_sqlite_db_path_relative(monkeypatch):
    monkeypatch.setenv("DB_URL", "sqlite:///./data/corvid.db")
    assert entrypoint._sqlite_db_path() == "/backend/data/corvid.db"


def test_sqlite_db_path_absolute(monkeypatch):
    monkeypatch.setenv("DB_URL", "sqlite:////custom/path/corvid.db")
    assert entrypoint._sqlite_db_path() == "/custom/path/corvid.db"


def test_sqlite_db_path_non_sqlite_backend(monkeypatch):
    monkeypatch.setenv("DB_URL", "postgresql+asyncpg://user:pass@host/db")
    assert entrypoint._sqlite_db_path() is None


def test_sqlite_db_path_defaults_when_unset(monkeypatch):
    monkeypatch.delenv("DB_URL", raising=False)
    assert entrypoint._sqlite_db_path() == "/backend/data/corvid.db"


def test_backup_database_skips_missing_db_file(monkeypatch, backup_dir):
    monkeypatch.setenv("DB_URL", "sqlite:////nonexistent/corvid.db")
    entrypoint._backup_database()
    assert not backup_dir.exists()


def test_backup_database_copies_db_and_wal_shm(tmp_path, monkeypatch, backup_dir):
    db_path = tmp_path / "corvid.db"
    db_path.write_bytes(b"main-db")
    (tmp_path / "corvid.db-wal").write_bytes(b"wal")
    (tmp_path / "corvid.db-shm").write_bytes(b"shm")
    monkeypatch.setenv("DB_URL", f"sqlite:///{db_path}")

    entrypoint._backup_database()

    snapshots = list(backup_dir.iterdir())
    assert len(snapshots) == 1
    copied = {f.name for f in snapshots[0].iterdir()}
    assert copied == {"corvid.db", "corvid.db-wal", "corvid.db-shm"}
    assert (snapshots[0] / "corvid.db").read_bytes() == b"main-db"


def test_backup_database_omits_missing_wal_shm(tmp_path, monkeypatch, backup_dir):
    db_path = tmp_path / "corvid.db"
    db_path.write_bytes(b"main-db")
    monkeypatch.setenv("DB_URL", f"sqlite:///{db_path}")

    entrypoint._backup_database()

    snapshots = list(backup_dir.iterdir())
    copied = {f.name for f in snapshots[0].iterdir()}
    assert copied == {"corvid.db"}


def test_prune_old_backups_keeps_only_the_last_n(backup_dir, monkeypatch):
    monkeypatch.setattr(entrypoint, "BACKUPS_TO_KEEP", 2)
    backup_dir.mkdir()
    for name in ["20260101T000000Z", "20260102T000000Z", "20260103T000000Z"]:
        (backup_dir / name).mkdir()

    entrypoint._prune_old_backups()

    assert sorted(os.listdir(backup_dir)) == ["20260102T000000Z", "20260103T000000Z"]


def test_prune_old_backups_noop_when_dir_missing(backup_dir):
    entrypoint._prune_old_backups()  # must not raise


def test_backup_then_prune_end_to_end(tmp_path, monkeypatch, backup_dir):
    monkeypatch.setattr(entrypoint, "BACKUPS_TO_KEEP", 1)
    db_path = tmp_path / "corvid.db"
    monkeypatch.setenv("DB_URL", f"sqlite:///{db_path}")

    for content in (b"v1", b"v2", b"v3"):
        db_path.write_bytes(content)
        entrypoint._backup_database()

    snapshots = list(backup_dir.iterdir())
    assert len(snapshots) == 1
    assert (snapshots[0] / "corvid.db").read_bytes() == b"v3"


if "docker_entrypoint" in sys.modules:
    del sys.modules["docker_entrypoint"]
