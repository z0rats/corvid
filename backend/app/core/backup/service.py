"""Export/import of a full app-state backup: the SQLite database plus the two
files needed to make sense of it (`.encryption_key`, optionally `.access_token`).

Scope deliberately excludes `data/logs/`, maigret's site database, and pyppeteer's
Chromium download - none of those are "settings and history", see
docs/adr/0010-backup-restore-design.md.

Restore only writes the extracted files to disk and reports `restart_required`;
it does not hot-swap the live SQLAlchemy engine. `os.replace` is an atomic rename,
so the currently running process's already-open connections keep working against
the pre-restore file (same inode, just unlinked from the path) until the operator
restarts the backend - at which point `docker-entrypoint.py`'s existing
`alembic upgrade head` step runs against the restored database, exactly like it
does for a normal deploy. See the ADR for why this was chosen over an in-process
hot-swap.
"""

import asyncio
import base64
import io
import json
import logging
import os
import sqlite3
import tarfile
import tempfile
from datetime import UTC, datetime
from pathlib import Path

from cryptography.fernet import Fernet, InvalidToken
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

from app.core.backup.schemas import BackupStatusResponse, RestoreResponse
from app.core.config.settings import settings
from app.core.database import engine
from app.core.exceptions import ApplicationError

logger = logging.getLogger(__name__)

_MANIFEST_NAME = "manifest.json"
_DB_MEMBER_NAME = "corvid.db"
_KEY_MEMBER_NAME = ".encryption_key"
_TOKEN_MEMBER_NAME = ".access_token"

_GZIP_MAGIC = b"\x1f\x8b"
_SALT_SIZE = 16
# OWASP-recommended minimum for PBKDF2-HMAC-SHA256 as of 2023.
_PBKDF2_ITERATIONS = 600_000

_BACKEND_DIR = Path(__file__).resolve().parents[3]


def _is_sqlite() -> bool:
    return engine.dialect.name == "sqlite"


def get_backup_status() -> BackupStatusResponse:
    return BackupStatusResponse(supported=_is_sqlite(), db_dialect=engine.dialect.name)


def _require_sqlite() -> None:
    if not _is_sqlite():
        raise ApplicationError(
            f"Backup/restore only supports the SQLite backend (configured: {engine.dialect.name}). "
            "Use your database's own dump/restore tooling instead - see "
            "docs/adr/0004-sqlite-only-postgres-unsupported.md.",
            status_code=501,
            error_code="BACKUP_UNSUPPORTED_DIALECT",
        )


def _known_alembic_revisions() -> set[str]:
    """Every revision Alembic's script directory knows about, valid or not-yet-applied.

    Used to reject a restore whose manifest names a revision this codebase has
    never heard of - a corrupted upload or a file that isn't a Corvid backup at
    all - without requiring the revision to equal the current head (an older,
    still-recognized backup is fine; `alembic upgrade head` on next startup
    brings it forward, same as any other upgrade).
    """
    from alembic.config import Config
    from alembic.script import ScriptDirectory

    cfg = Config(str(_BACKEND_DIR / "alembic.ini"))
    script = ScriptDirectory.from_config(cfg)
    return {rev.revision for rev in script.walk_revisions()}


def _sqlite_path() -> str:
    path = str(engine.url.database)
    return path if os.path.isabs(path) else os.path.normpath(os.path.join(os.getcwd(), path))


def _vacuum_into_sync(source_path: str, dest_path: str) -> None:
    """Write a consistent, standalone snapshot of `source_path` to `dest_path`.

    `VACUUM INTO` produces a plain (non-WAL) single file with no separate
    `-wal`/`-shm` sidecars, so a backup archive never needs to carry those -
    unlike `docker-entrypoint.py`'s pre-migration snapshot, which is a raw file
    copy taken before the app (and this VACUUM path) is even available.
    `isolation_level=None` puts the stdlib driver in autocommit mode, since
    SQLite refuses to run VACUUM inside a transaction.
    """
    conn = sqlite3.connect(source_path, isolation_level=None)
    try:
        conn.execute("VACUUM INTO ?", (dest_path,))
    finally:
        conn.close()


def _integrity_check_sync(db_path: str) -> str | None:
    """Return None if `PRAGMA integrity_check` passes, else the first problem reported.

    A file that isn't a SQLite database at all (garbage, an unrelated file type)
    raises `sqlite3.DatabaseError` on the very first statement rather than
    returning a row - both are treated as an integrity failure here.
    """
    conn = sqlite3.connect(db_path)
    try:
        row = conn.execute("PRAGMA integrity_check").fetchone()
        return None if row and row[0] == "ok" else str(row[0] if row else "unknown error")
    except sqlite3.DatabaseError as exc:
        return str(exc)
    finally:
        conn.close()


def _stamped_alembic_revision_sync(db_path: str) -> str | None:
    conn = sqlite3.connect(db_path)
    try:
        row = conn.execute("SELECT version_num FROM alembic_version").fetchone()
        return row[0] if row else None
    except sqlite3.OperationalError:
        return None
    finally:
        conn.close()


def _derive_passphrase_key(passphrase: str, salt: bytes) -> bytes:
    kdf = PBKDF2HMAC(algorithm=hashes.SHA256(), length=32, salt=salt, iterations=_PBKDF2_ITERATIONS)
    return base64.urlsafe_b64encode(kdf.derive(passphrase.encode("utf-8")))


def _encrypt_archive(data: bytes, passphrase: str) -> bytes:
    salt = os.urandom(_SALT_SIZE)
    key = _derive_passphrase_key(passphrase, salt)
    return salt + Fernet(key).encrypt(data)


def _decrypt_archive(blob: bytes, passphrase: str) -> bytes:
    salt, token = blob[:_SALT_SIZE], blob[_SALT_SIZE:]
    key = _derive_passphrase_key(passphrase, salt)
    try:
        return Fernet(key).decrypt(token)
    except InvalidToken as exc:
        raise ApplicationError(
            "Incorrect passphrase, or the backup file is corrupted.",
            status_code=400,
            error_code="BACKUP_BAD_PASSPHRASE",
        ) from exc


def _add_bytes(tar: tarfile.TarFile, name: str, data: bytes) -> None:
    info = tarfile.TarInfo(name=name)
    info.size = len(data)
    info.mtime = int(datetime.now(UTC).timestamp())
    tar.addfile(info, io.BytesIO(data))


async def export_backup(*, include_access_token: bool, passphrase: str | None) -> tuple[bytes, str]:
    """Build a backup archive. Returns (content_bytes, filename)."""
    _require_sqlite()

    key_path = os.path.join(settings.data_dir, _KEY_MEMBER_NAME)
    if not os.path.exists(key_path):
        raise ApplicationError(
            "No encryption key file found - nothing has been encrypted at rest yet, "
            "or the deployment doesn't persist one at the expected path.",
            status_code=409,
            error_code="BACKUP_NO_ENCRYPTION_KEY",
        )

    with tempfile.TemporaryDirectory() as tmpdir:
        snapshot_path = os.path.join(tmpdir, _DB_MEMBER_NAME)
        await asyncio.to_thread(_vacuum_into_sync, _sqlite_path(), snapshot_path)
        alembic_revision = await asyncio.to_thread(_stamped_alembic_revision_sync, snapshot_path)

        manifest = {
            "app_version": settings.api.version,
            "db_dialect": engine.dialect.name,
            "alembic_revision": alembic_revision,
            "created_at": datetime.now(UTC).isoformat(),
            "includes_access_token": include_access_token,
        }

        buffer = io.BytesIO()
        with tarfile.open(fileobj=buffer, mode="w:gz") as tar:
            _add_bytes(tar, _MANIFEST_NAME, json.dumps(manifest, indent=2).encode("utf-8"))
            tar.add(snapshot_path, arcname=_DB_MEMBER_NAME)
            tar.add(key_path, arcname=_KEY_MEMBER_NAME)
            if include_access_token:
                token_path = os.path.join(settings.data_dir, _TOKEN_MEMBER_NAME)
                if os.path.exists(token_path):
                    tar.add(token_path, arcname=_TOKEN_MEMBER_NAME)

        archive = buffer.getvalue()

    if passphrase:
        archive = _encrypt_archive(archive, passphrase)

    timestamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    ext = "tar.gz.enc" if passphrase else "tar.gz"
    return archive, f"corvid-backup-{timestamp}.{ext}"


def _read_member(tar: tarfile.TarFile, name: str) -> bytes:
    """Read one named member's bytes.

    Uses `extractfile(name)` rather than `extractall()`/iterating arbitrary
    member names, so a crafted archive can't write anywhere outside these
    fixed, hardcoded names (the classic tar path-traversal class of bug).
    """
    member = tar.extractfile(name)
    if member is None:
        raise ApplicationError(
            f"Backup archive is missing required entry: {name}",
            status_code=400,
            error_code="BACKUP_INVALID_ARCHIVE",
        )
    return member.read()


def _validate_manifest(manifest: dict) -> None:
    if manifest.get("db_dialect") != "sqlite":
        raise ApplicationError(
            f"Backup was taken from a {manifest.get('db_dialect')!r} database; "
            "this deployment runs sqlite.",
            status_code=400,
            error_code="BACKUP_DIALECT_MISMATCH",
        )
    revision = manifest.get("alembic_revision")
    if revision and revision not in _known_alembic_revisions():
        raise ApplicationError(
            "Backup's schema revision is not recognized by this install - it may not be a "
            "Corvid backup, or comes from an incompatible fork/version.",
            status_code=400,
            error_code="BACKUP_UNKNOWN_REVISION",
        )


def _atomic_write(dest_path: str, data: bytes, tmpdir: str, tag: str) -> None:
    staged = os.path.join(tmpdir, tag)
    fd = os.open(staged, os.O_CREAT | os.O_WRONLY | os.O_EXCL, 0o600)
    with os.fdopen(fd, "wb") as f:
        f.write(data)
    os.replace(staged, dest_path)


async def restore_backup(archive_bytes: bytes, *, passphrase: str | None) -> RestoreResponse:
    _require_sqlite()

    raw = archive_bytes
    if not raw.startswith(_GZIP_MAGIC):
        if not passphrase:
            raise ApplicationError(
                "This backup is passphrase-protected - provide the passphrase to restore it.",
                status_code=400,
                error_code="BACKUP_PASSPHRASE_REQUIRED",
            )
        raw = _decrypt_archive(raw, passphrase)

    try:
        with tarfile.open(fileobj=io.BytesIO(raw), mode="r:gz") as tar:
            manifest = json.loads(_read_member(tar, _MANIFEST_NAME))
            _validate_manifest(manifest)

            db_bytes = _read_member(tar, _DB_MEMBER_NAME)
            key_bytes = _read_member(tar, _KEY_MEMBER_NAME)
            has_token = _TOKEN_MEMBER_NAME in tar.getnames()
            token_bytes = _read_member(tar, _TOKEN_MEMBER_NAME) if has_token else None
    except tarfile.TarError as exc:
        raise ApplicationError(
            "Backup file is not a valid archive (wrong passphrase, or a corrupted/unrelated file).",
            status_code=400,
            error_code="BACKUP_INVALID_ARCHIVE",
        ) from exc

    with tempfile.TemporaryDirectory() as tmpdir:
        staged_db = os.path.join(tmpdir, _DB_MEMBER_NAME)
        with open(staged_db, "wb") as f:
            f.write(db_bytes)

        problem = await asyncio.to_thread(_integrity_check_sync, staged_db)
        if problem:
            raise ApplicationError(
                f"Backup's database failed integrity check: {problem}",
                status_code=400,
                error_code="BACKUP_INTEGRITY_CHECK_FAILED",
            )

        db_path = _sqlite_path()
        os.replace(staged_db, db_path)
        for suffix in ("-wal", "-shm"):
            try:
                os.remove(db_path + suffix)
            except FileNotFoundError:
                pass

        key_path = os.path.join(settings.data_dir, _KEY_MEMBER_NAME)
        _atomic_write(key_path, key_bytes, tmpdir, "key")

        if token_bytes is not None:
            token_path = os.path.join(settings.data_dir, _TOKEN_MEMBER_NAME)
            _atomic_write(token_path, token_bytes, tmpdir, "token")

    logger.warning(
        "Restored backup (manifest created_at=%s, alembic_revision=%s). "
        "Restart the backend for the restored state to take effect.",
        manifest.get("created_at"),
        manifest.get("alembic_revision"),
    )
    return RestoreResponse(access_token_restored=token_bytes is not None)
