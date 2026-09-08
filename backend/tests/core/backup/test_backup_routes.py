"""HTTP-level coverage for backup/routers.py. The service functions themselves
are covered by test_backup_service.py, so these patch export_backup/restore_backup/
get_backup_status to isolate request parsing, the confirm-phrase gate, and error
mapping."""

import contextlib
from collections.abc import AsyncGenerator

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.alerts.models.alerts_models import Alert
from app.core.backup import routers as backup_routes
from app.core.backup.schemas import BackupStatusResponse, RestoreResponse
from app.core.dependencies import get_db, get_read_db
from app.core.exceptions import ApplicationError, register_exception_handlers
from app.core.settings.telegram.models.telegram_settings_models import TelegramSettings


@pytest.fixture
def client(monkeypatch, make_session_factory):
    # export/restore now raise an alert (in-app + optional Telegram, see
    # alerts_service.raise_alert) on success/failure - route both the
    # request-scoped SessionDep and the routers' own managed_session() (used for
    # the failure-path/restore-success alerts, see routers.py's comments on why)
    # at the same in-memory DB, so nothing here touches the real app database.
    factory = make_session_factory([Alert.__table__, TelegramSettings.__table__])

    async def _get_db() -> AsyncGenerator[AsyncSession]:
        async with factory() as db:
            yield db
            await db.commit()

    @contextlib.asynccontextmanager
    async def fake_managed_session():
        async with factory() as db:
            yield db
            await db.commit()

    monkeypatch.setattr(backup_routes, "managed_session", fake_managed_session)

    app = FastAPI()
    register_exception_handlers(app)
    app.include_router(backup_routes.router)
    app.dependency_overrides[get_db] = _get_db
    app.dependency_overrides[get_read_db] = _get_db
    return TestClient(app)


def test_status_endpoint_returns_service_result(client, monkeypatch):
    monkeypatch.setattr(
        backup_routes,
        "get_backup_status",
        lambda: BackupStatusResponse(supported=True, db_dialect="sqlite"),
    )

    response = client.get("/api/backup/status")

    assert response.status_code == 200
    assert response.json() == {"supported": True, "db_dialect": "sqlite"}


def test_export_endpoint_streams_archive_with_content_disposition(client, monkeypatch):
    async def fake_export(*, include_access_token, passphrase):
        return b"fake-archive-bytes", "corvid-backup-20260101T000000Z.tar.gz"

    monkeypatch.setattr(backup_routes, "export_backup", fake_export)

    response = client.post("/api/backup/export", json={})

    assert response.status_code == 200
    assert response.content == b"fake-archive-bytes"
    assert (
        'filename="corvid-backup-20260101T000000Z.tar.gz"'
        in response.headers["content-disposition"]
    )


def test_export_endpoint_passes_options_through(client, monkeypatch):
    captured = {}

    async def fake_export(*, include_access_token, passphrase):
        captured["include_access_token"] = include_access_token
        captured["passphrase"] = passphrase
        return b"x", "f.tar.gz.enc"

    monkeypatch.setattr(backup_routes, "export_backup", fake_export)

    client.post("/api/backup/export", json={"include_access_token": True, "passphrase": "hunter2"})

    assert captured == {"include_access_token": True, "passphrase": "hunter2"}


def test_export_endpoint_defaults_omit_access_token_and_passphrase(client, monkeypatch):
    captured = {}

    async def fake_export(*, include_access_token, passphrase):
        captured["include_access_token"] = include_access_token
        captured["passphrase"] = passphrase
        return b"x", "f.tar.gz"

    monkeypatch.setattr(backup_routes, "export_backup", fake_export)

    client.post("/api/backup/export", json={})

    assert captured == {"include_access_token": False, "passphrase": None}


def test_export_endpoint_maps_application_error(client, monkeypatch):
    async def fake_export(*, include_access_token, passphrase):
        raise ApplicationError("nope", status_code=501, error_code="BACKUP_UNSUPPORTED_DIALECT")

    monkeypatch.setattr(backup_routes, "export_backup", fake_export)

    response = client.post("/api/backup/export", json={})

    assert response.status_code == 501
    assert response.json()["error_code"] == "BACKUP_UNSUPPORTED_DIALECT"


def test_restore_endpoint_rejects_missing_confirmation(client):
    response = client.post(
        "/api/backup/restore",
        files={"file": ("backup.tar.gz", b"data", "application/gzip")},
        data={"confirm": "please"},
    )

    assert response.status_code == 400
    assert response.json()["error_code"] == "BACKUP_RESTORE_NOT_CONFIRMED"


def test_restore_endpoint_calls_service_when_confirmed(client, monkeypatch):
    captured = {}

    async def fake_restore(archive_bytes, *, passphrase):
        captured["archive_bytes"] = archive_bytes
        captured["passphrase"] = passphrase
        return RestoreResponse(access_token_restored=True)

    monkeypatch.setattr(backup_routes, "restore_backup", fake_restore)

    response = client.post(
        "/api/backup/restore",
        files={"file": ("backup.tar.gz", b"archive-content", "application/gzip")},
        data={"confirm": "RESTORE", "passphrase": "hunter2"},
    )

    assert response.status_code == 200
    assert response.json() == {"restart_required": True, "access_token_restored": True}
    assert captured == {"archive_bytes": b"archive-content", "passphrase": "hunter2"}


def test_restore_endpoint_maps_application_error(client, monkeypatch):
    async def fake_restore(archive_bytes, *, passphrase):
        raise ApplicationError(
            "bad passphrase", status_code=400, error_code="BACKUP_BAD_PASSPHRASE"
        )

    monkeypatch.setattr(backup_routes, "restore_backup", fake_restore)

    response = client.post(
        "/api/backup/restore",
        files={"file": ("backup.tar.gz", b"data", "application/gzip")},
        data={"confirm": "RESTORE"},
    )

    assert response.status_code == 400
    assert response.json()["error_code"] == "BACKUP_BAD_PASSPHRASE"


def test_restore_endpoint_requires_file(client):
    response = client.post("/api/backup/restore", data={"confirm": "RESTORE"})

    assert response.status_code == 422


def test_restore_endpoint_requires_confirm_field(client):
    response = client.post(
        "/api/backup/restore",
        files={"file": ("backup.tar.gz", b"data", "application/gzip")},
    )

    assert response.status_code == 422
