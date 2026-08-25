"""Business-logic coverage for app/core/backup/service.py.

Uses a lightweight `_FakeEngine` double (a `.url.database`/`.dialect.name` pair)
rather than a real SQLAlchemy engine, so tests can freely point the module at
different on-disk sqlite files (and a fake non-sqlite dialect) without needing
a live async engine or session.
"""

import asyncio
import io
import json
import sqlite3
import tarfile
from pathlib import Path

import pytest

from app.core.backup import service
from app.core.exceptions import ApplicationError


def _run(coro):
    return asyncio.run(coro)


class _FakeURL:
    def __init__(self, database: str) -> None:
        self.database = database


class _FakeDialect:
    def __init__(self, name: str) -> None:
        self.name = name


class _FakeEngine:
    def __init__(self, db_path, dialect_name: str = "sqlite") -> None:
        self.url = _FakeURL(str(db_path))
        self.dialect = _FakeDialect(dialect_name)


def _make_sqlite_db(path: Path, revision: str, rows=(("hello",),)) -> None:
    conn = sqlite3.connect(path)
    try:
        conn.execute("CREATE TABLE alembic_version (version_num VARCHAR(32) NOT NULL)")
        conn.execute("INSERT INTO alembic_version VALUES (?)", (revision,))
        conn.execute("CREATE TABLE widget (name TEXT)")
        conn.executemany("INSERT INTO widget VALUES (?)", rows)
        conn.commit()
    finally:
        conn.close()


def _use(monkeypatch, db_path, data_dir, dialect_name: str = "sqlite") -> None:
    monkeypatch.setattr(service, "engine", _FakeEngine(db_path, dialect_name))
    monkeypatch.setattr(service.settings, "data_dir", str(data_dir))


def _tar_names(content: bytes) -> set[str]:
    with tarfile.open(fileobj=io.BytesIO(content), mode="r:gz") as tar:
        return set(tar.getnames())


def _replace_manifest_field(content: bytes, field: str, value) -> bytes:
    with tarfile.open(fileobj=io.BytesIO(content), mode="r:gz") as tar:
        members = {m.name: tar.extractfile(m).read() for m in tar.getmembers()}
    manifest = json.loads(members["manifest.json"])
    manifest[field] = value
    members["manifest.json"] = json.dumps(manifest).encode("utf-8")
    return _rebuild_tar(members)


def _replace_member(content: bytes, name: str, data: bytes) -> bytes:
    with tarfile.open(fileobj=io.BytesIO(content), mode="r:gz") as tar:
        members = {m.name: tar.extractfile(m).read() for m in tar.getmembers()}
    members[name] = data
    return _rebuild_tar(members)


def _rebuild_tar(members: dict[str, bytes]) -> bytes:
    buffer = io.BytesIO()
    with tarfile.open(fileobj=buffer, mode="w:gz") as tar:
        for name, data in members.items():
            info = tarfile.TarInfo(name=name)
            info.size = len(data)
            tar.addfile(info, io.BytesIO(data))
    return buffer.getvalue()


@pytest.fixture
def known_revision() -> str:
    return next(iter(service._known_alembic_revisions()))


@pytest.fixture
def source(tmp_path, known_revision) -> Path:
    data_dir = tmp_path / "source"
    data_dir.mkdir()
    _make_sqlite_db(data_dir / "corvid.db", known_revision)
    (data_dir / ".encryption_key").write_text("fake-key-material")
    (data_dir / ".access_token").write_text("fake-token-material")
    return data_dir


@pytest.fixture
def dest(tmp_path) -> Path:
    d = tmp_path / "dest"
    d.mkdir()
    return d


# --- get_backup_status ---------------------------------------------------


def test_status_reports_supported_for_sqlite(monkeypatch, source):
    _use(monkeypatch, source / "corvid.db", source)

    status = service.get_backup_status()

    assert status.supported is True
    assert status.db_dialect == "sqlite"


def test_status_reports_unsupported_for_non_sqlite(monkeypatch, source):
    _use(monkeypatch, source / "corvid.db", source, dialect_name="postgresql")

    assert service.get_backup_status().supported is False


# --- export_backup --------------------------------------------------------


def test_export_rejects_non_sqlite_dialect(monkeypatch, source):
    _use(monkeypatch, source / "corvid.db", source, dialect_name="postgresql")

    with pytest.raises(ApplicationError) as exc_info:
        _run(service.export_backup(include_access_token=False, passphrase=None))
    assert exc_info.value.status_code == 501
    assert exc_info.value.error_code == "BACKUP_UNSUPPORTED_DIALECT"


def test_export_requires_encryption_key_file(monkeypatch, tmp_path, known_revision):
    db_path = tmp_path / "corvid.db"
    _make_sqlite_db(db_path, known_revision)
    _use(monkeypatch, db_path, tmp_path)  # no .encryption_key written

    with pytest.raises(ApplicationError) as exc_info:
        _run(service.export_backup(include_access_token=False, passphrase=None))
    assert exc_info.value.error_code == "BACKUP_NO_ENCRYPTION_KEY"


def test_export_produces_plain_gzip_archive_without_passphrase(monkeypatch, source):
    _use(monkeypatch, source / "corvid.db", source)

    content, filename = _run(service.export_backup(include_access_token=False, passphrase=None))

    assert content.startswith(service._GZIP_MAGIC)
    assert filename.endswith(".tar.gz")


def test_export_encrypts_when_passphrase_given(monkeypatch, source):
    _use(monkeypatch, source / "corvid.db", source)

    content, filename = _run(
        service.export_backup(include_access_token=False, passphrase="hunter2")
    )

    assert not content.startswith(service._GZIP_MAGIC)
    assert filename.endswith(".tar.gz.enc")


def test_export_omits_access_token_by_default(monkeypatch, source):
    _use(monkeypatch, source / "corvid.db", source)

    content, _ = _run(service.export_backup(include_access_token=False, passphrase=None))

    assert service._TOKEN_MEMBER_NAME not in _tar_names(content)


def test_export_includes_access_token_when_requested(monkeypatch, source):
    _use(monkeypatch, source / "corvid.db", source)

    content, _ = _run(service.export_backup(include_access_token=True, passphrase=None))

    with tarfile.open(fileobj=io.BytesIO(content), mode="r:gz") as tar:
        assert service._TOKEN_MEMBER_NAME in tar.getnames()
        assert tar.extractfile(service._TOKEN_MEMBER_NAME).read() == b"fake-token-material"


def test_export_manifest_records_stamped_alembic_revision(monkeypatch, source, known_revision):
    _use(monkeypatch, source / "corvid.db", source)

    content, _ = _run(service.export_backup(include_access_token=False, passphrase=None))

    with tarfile.open(fileobj=io.BytesIO(content), mode="r:gz") as tar:
        manifest = json.loads(tar.extractfile("manifest.json").read())
    assert manifest["alembic_revision"] == known_revision
    assert manifest["db_dialect"] == "sqlite"
    assert manifest["includes_access_token"] is False


def test_exported_db_is_a_consistent_standalone_snapshot(monkeypatch, source):
    """VACUUM INTO's output must not need separate -wal/-shm sidecars."""
    _use(monkeypatch, source / "corvid.db", source)

    content, _ = _run(service.export_backup(include_access_token=False, passphrase=None))

    names = _tar_names(content)
    assert "corvid.db-wal" not in names
    assert "corvid.db-shm" not in names


# --- restore_backup --------------------------------------------------------


def test_restore_round_trip_writes_db_and_key(monkeypatch, source, dest):
    _use(monkeypatch, source / "corvid.db", source)
    content, _ = _run(service.export_backup(include_access_token=False, passphrase=None))

    dest_db = dest / "corvid.db"
    _use(monkeypatch, dest_db, dest)
    result = _run(service.restore_backup(content, passphrase=None))

    assert result.access_token_restored is False
    conn = sqlite3.connect(dest_db)
    try:
        rows = conn.execute("SELECT name FROM widget").fetchall()
    finally:
        conn.close()
    assert rows == [("hello",)]
    assert (dest / ".encryption_key").read_text() == "fake-key-material"
    assert not (dest / ".access_token").exists()


def test_restore_writes_access_token_only_when_included(monkeypatch, source, dest):
    _use(monkeypatch, source / "corvid.db", source)
    content, _ = _run(service.export_backup(include_access_token=True, passphrase=None))

    dest_db = dest / "corvid.db"
    _use(monkeypatch, dest_db, dest)
    result = _run(service.restore_backup(content, passphrase=None))

    assert result.access_token_restored is True
    assert (dest / ".access_token").read_text() == "fake-token-material"


def test_restore_round_trip_with_passphrase(monkeypatch, source, dest):
    _use(monkeypatch, source / "corvid.db", source)
    content, _ = _run(service.export_backup(include_access_token=False, passphrase="hunter2"))

    dest_db = dest / "corvid.db"
    _use(monkeypatch, dest_db, dest)
    _run(service.restore_backup(content, passphrase="hunter2"))

    assert (dest / ".encryption_key").read_text() == "fake-key-material"


def test_restore_rejects_wrong_passphrase(monkeypatch, source, dest):
    _use(monkeypatch, source / "corvid.db", source)
    content, _ = _run(service.export_backup(include_access_token=False, passphrase="hunter2"))

    dest_db = dest / "corvid.db"
    _use(monkeypatch, dest_db, dest)
    with pytest.raises(ApplicationError) as exc_info:
        _run(service.restore_backup(content, passphrase="wrong"))
    assert exc_info.value.error_code == "BACKUP_BAD_PASSPHRASE"


def test_restore_requires_passphrase_for_encrypted_archive(monkeypatch, source, dest):
    _use(monkeypatch, source / "corvid.db", source)
    content, _ = _run(service.export_backup(include_access_token=False, passphrase="hunter2"))

    dest_db = dest / "corvid.db"
    _use(monkeypatch, dest_db, dest)
    with pytest.raises(ApplicationError) as exc_info:
        _run(service.restore_backup(content, passphrase=None))
    assert exc_info.value.error_code == "BACKUP_PASSPHRASE_REQUIRED"


def test_restore_rejects_non_sqlite_dialect(monkeypatch, source, dest):
    _use(monkeypatch, source / "corvid.db", source)
    content, _ = _run(service.export_backup(include_access_token=False, passphrase=None))

    _use(monkeypatch, dest / "corvid.db", dest, dialect_name="postgresql")
    with pytest.raises(ApplicationError) as exc_info:
        _run(service.restore_backup(content, passphrase=None))
    assert exc_info.value.status_code == 501


def test_restore_rejects_dialect_mismatch_in_manifest(monkeypatch, source, dest):
    _use(monkeypatch, source / "corvid.db", source)
    content, _ = _run(service.export_backup(include_access_token=False, passphrase=None))
    tampered = _replace_manifest_field(content, "db_dialect", "postgresql")

    _use(monkeypatch, dest / "corvid.db", dest)
    with pytest.raises(ApplicationError) as exc_info:
        _run(service.restore_backup(tampered, passphrase=None))
    assert exc_info.value.error_code == "BACKUP_DIALECT_MISMATCH"


def test_restore_rejects_unknown_alembic_revision(monkeypatch, source, dest):
    _use(monkeypatch, source / "corvid.db", source)
    content, _ = _run(service.export_backup(include_access_token=False, passphrase=None))
    tampered = _replace_manifest_field(content, "alembic_revision", "not-a-real-revision")

    _use(monkeypatch, dest / "corvid.db", dest)
    with pytest.raises(ApplicationError) as exc_info:
        _run(service.restore_backup(tampered, passphrase=None))
    assert exc_info.value.error_code == "BACKUP_UNKNOWN_REVISION"


def test_restore_rejects_corrupted_db_member(monkeypatch, source, dest):
    _use(monkeypatch, source / "corvid.db", source)
    content, _ = _run(service.export_backup(include_access_token=False, passphrase=None))
    tampered = _replace_member(content, service._DB_MEMBER_NAME, b"not a sqlite file")

    _use(monkeypatch, dest / "corvid.db", dest)
    with pytest.raises(ApplicationError) as exc_info:
        _run(service.restore_backup(tampered, passphrase=None))
    assert exc_info.value.error_code == "BACKUP_INTEGRITY_CHECK_FAILED"


def test_restore_rejects_corrupted_gzip_archive(monkeypatch, source, dest):
    _use(monkeypatch, source / "corvid.db", source)

    garbage = service._GZIP_MAGIC + b"this is not a valid gzip/tar stream"
    _use(monkeypatch, dest / "corvid.db", dest)
    with pytest.raises(ApplicationError) as exc_info:
        _run(service.restore_backup(garbage, passphrase=None))
    assert exc_info.value.error_code == "BACKUP_INVALID_ARCHIVE"


def test_restore_treats_non_gzip_input_without_passphrase_as_needing_one(monkeypatch, source, dest):
    _use(monkeypatch, dest / "corvid.db", dest)

    with pytest.raises(ApplicationError) as exc_info:
        _run(service.restore_backup(b"not a tar archive at all", passphrase=None))
    assert exc_info.value.error_code == "BACKUP_PASSPHRASE_REQUIRED"


def test_restore_leaves_previously_open_handle_on_the_old_file(monkeypatch, source, dest):
    """The whole point of using os.replace: a file descriptor already open against
    the pre-restore db keeps reading the old content after the swap, since rename
    doesn't touch already-open file handles - this is what makes the
    restart-required design safe without disposing the live engine."""
    _use(monkeypatch, source / "corvid.db", source)
    content, _ = _run(service.export_backup(include_access_token=False, passphrase=None))

    dest_db = dest / "corvid.db"
    _make_sqlite_db(dest_db, "irrelevant-will-be-overwritten", rows=(("pre-restore",),))
    held_open = open(dest_db, "rb")
    try:
        original_bytes = held_open.read()

        _use(monkeypatch, dest_db, dest)
        _run(service.restore_backup(content, passphrase=None))

        held_open.seek(0)
        assert held_open.read() == original_bytes
        assert dest_db.read_bytes() != original_bytes
    finally:
        held_open.close()
