"""HTTP-level coverage for telegram_settings_routes.py: the base GET/PUT pair
built on build_singleton_settings_router, plus the hand-written /test endpoint
that sends a real message through telegram_client (mocked here)."""

from collections.abc import AsyncGenerator

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_db, get_read_db
from app.core.exceptions import register_exception_handlers
from app.core.settings.telegram.models.telegram_settings_models import TelegramSettings
from app.core.settings.telegram.routers.telegram_settings_routes import router
from app.core.settings.telegram.service import telegram_settings_service
from app.core.settings.telegram.service.telegram_client import TelegramDeliveryError


@pytest.fixture
def client(make_session_factory):
    session_factory = make_session_factory([TelegramSettings.__table__])

    async def _get_db() -> AsyncGenerator[AsyncSession]:
        async with session_factory() as db:
            yield db
            await db.commit()

    app = FastAPI()
    register_exception_handlers(app)
    app.include_router(router)
    app.dependency_overrides[get_db] = _get_db
    app.dependency_overrides[get_read_db] = _get_db
    return TestClient(app)


class TestGetTelegramSettings:
    def test_creates_and_returns_defaults(self, client):
        response = client.get("/api/settings/telegram")

        assert response.status_code == 200
        body = response.json()
        assert body["enabled"] is False
        assert body["bot_token"] == ""
        assert body["notify_scan_events"] is True
        assert body["notify_job_failures"] is True
        assert body["notify_newsfeed_matches"] is True


class TestUpdateTelegramSettings:
    def test_updates_provided_fields(self, client):
        response = client.put(
            "/api/settings/telegram",
            json={"bot_token": "123:abc", "chat_id": "42", "enabled": True},
        )

        assert response.status_code == 200
        body = response.json()
        assert body["bot_token"] == "123:abc"
        assert body["chat_id"] == "42"
        assert body["enabled"] is True

    def test_omitted_fields_are_left_unchanged(self, client):
        client.put("/api/settings/telegram", json={"notify_scan_events": False})

        response = client.put("/api/settings/telegram", json={"notify_job_failures": False})

        body = response.json()
        assert body["notify_scan_events"] is False
        assert body["notify_job_failures"] is False


class TestSendTestMessage:
    def test_not_configured_returns_400(self, client):
        response = client.post("/api/settings/telegram/test")

        assert response.status_code == 400
        assert response.json()["error_code"] == "TELEGRAM_NOT_CONFIGURED"

    def test_delivers_through_the_configured_settings(self, client, monkeypatch):
        client.put("/api/settings/telegram", json={"bot_token": "123:abc", "chat_id": "42"})

        calls = []

        async def fake_send(bot_token, chat_id, text):
            calls.append((bot_token, chat_id, text))

        monkeypatch.setattr(telegram_settings_service, "send_telegram_message", fake_send)

        response = client.post("/api/settings/telegram/test")

        assert response.status_code == 200
        assert response.json()["sent"] is True
        assert calls == [("123:abc", "42", telegram_settings_service.TEST_MESSAGE)]

    def test_delivery_failure_returns_502(self, client, monkeypatch):
        client.put("/api/settings/telegram", json={"bot_token": "123:abc", "chat_id": "42"})

        async def fake_send(bot_token, chat_id, text):
            raise TelegramDeliveryError("boom")

        monkeypatch.setattr(telegram_settings_service, "send_telegram_message", fake_send)

        response = client.post("/api/settings/telegram/test")

        assert response.status_code == 502
        assert response.json()["error_code"] == "TELEGRAM_TEST_FAILED"
