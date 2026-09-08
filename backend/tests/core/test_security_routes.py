"""HTTP-level coverage for security/routes.py's access-token regeneration
endpoint. raise_alert is mocked here - its own delivery behavior is covered by
tests/core/alerts/."""

from collections.abc import AsyncGenerator

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config.settings import settings
from app.core.dependencies import get_db
from app.core.exceptions import register_exception_handlers
from app.core.security import access_control, routes
from app.core.security.routes import router


@pytest.fixture
def client(make_session_factory, monkeypatch):
    session_factory = make_session_factory([])

    async def _get_db() -> AsyncGenerator[AsyncSession]:
        async with session_factory() as db:
            yield db
            await db.commit()

    app = FastAPI()
    register_exception_handlers(app)
    app.include_router(router)
    app.dependency_overrides[get_db] = _get_db

    monkeypatch.setattr(settings.api, "access_token", "")
    access_control.get_access_token.cache_clear()
    yield TestClient(app)
    access_control.get_access_token.cache_clear()


def test_regenerate_returns_a_new_token_and_raises_an_alert(tmp_path, monkeypatch, client):
    monkeypatch.setattr(settings, "data_dir", str(tmp_path))
    old_token = access_control.get_access_token()

    alert_calls = []

    async def fake_raise_alert(db, module, title, message, **kwargs):
        alert_calls.append((module, title, message))

    monkeypatch.setattr(routes, "raise_alert", fake_raise_alert)

    response = client.post("/api/settings/access-token/regenerate")

    assert response.status_code == 200
    new_token = response.json()["access_token"]
    assert new_token and new_token != old_token
    assert access_control.get_access_token() == new_token
    assert len(alert_calls) == 1
    assert alert_calls[0][0] == "security"


def test_regenerate_is_blocked_when_env_var_pins_a_fixed_token(monkeypatch, client):
    monkeypatch.setattr(settings.api, "access_token", "fixed-from-env")

    response = client.post("/api/settings/access-token/regenerate")

    assert response.status_code == 409
    assert response.json()["error_code"] == "ACCESS_TOKEN_FIXED_BY_ENV"
