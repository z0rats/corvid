"""Coverage for the alert (in-app + optional Telegram, see alerts_service.raise_alert)
raised by create/update/delete on /api/apikeys - a credential add/change/remove is
treated as a security-relevant event. The two narrow is_active/bulk_ioc_lookup-only
PATCH endpoints deliberately do NOT raise one (routine UI toggles, not credential
changes) - see api_keys_settings_routes.py's update_apikey.
"""

from collections.abc import AsyncGenerator

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.alerts.models.alerts_models import Alert
from app.core.dependencies import get_db, get_read_db
from app.core.settings.api_keys.models.api_keys_settings_models import Apikey
from app.core.settings.api_keys.routers import api_keys_settings_routes
from app.core.settings.telegram.models.telegram_settings_models import TelegramSettings
from tests.conftest import run as _run


@pytest.fixture
def factory(make_session_factory):
    return make_session_factory([Apikey.__table__, Alert.__table__, TelegramSettings.__table__])


@pytest.fixture
def client(factory):
    async def _get_db() -> AsyncGenerator[AsyncSession]:
        async with factory() as db:
            yield db
            await db.commit()

    app = FastAPI()
    app.include_router(api_keys_settings_routes.router)
    app.dependency_overrides[get_db] = _get_db
    app.dependency_overrides[get_read_db] = _get_db
    return TestClient(app)


async def _alert_titles(factory):
    async with factory() as db:
        result = await db.execute(select(Alert.title).order_by(Alert.id))
        return list(result.scalars().all())


class TestCreateApikeyAlert:
    def test_raises_alert_naming_the_provider_not_the_key(self, client, factory):
        response = client.post(
            "/api/apikeys", json={"name": "virustotal", "key": "super-secret-value"}
        )

        assert response.status_code == 201
        titles = _run(_alert_titles(factory))
        assert titles == ["API key added"]

        async def _message():
            async with factory() as db:
                result = await db.execute(select(Alert.message))
                return result.scalar_one()

        message = _run(_message())
        assert "virustotal" in message
        assert "super-secret-value" not in message


class TestUpdateApikeyAlert:
    def test_key_value_change_raises_alert(self, client, factory):
        client.post("/api/apikeys", json={"name": "shodan", "key": "old-key"})

        response = client.patch("/api/apikeys/shodan", json={"key": "new-key"})

        assert response.status_code == 200
        titles = _run(_alert_titles(factory))
        assert titles == ["API key added", "API key updated"]

    def test_toggling_only_is_active_does_not_raise_an_alert(self, client, factory):
        client.post("/api/apikeys", json={"name": "shodan", "key": "old-key"})

        response = client.patch("/api/apikeys/shodan", json={"is_active": True})

        assert response.status_code == 200
        assert _run(_alert_titles(factory)) == ["API key added"]

    def test_dedicated_is_active_endpoint_does_not_raise_an_alert(self, client, factory):
        client.post("/api/apikeys", json={"name": "shodan", "key": "old-key"})

        response = client.patch("/api/apikeys/shodan/is_active", json={"is_active": True})

        assert response.status_code == 200
        assert _run(_alert_titles(factory)) == ["API key added"]

    def test_dedicated_bulk_lookup_endpoint_does_not_raise_an_alert(self, client, factory):
        client.post("/api/apikeys", json={"name": "shodan", "key": "old-key"})

        response = client.patch(
            "/api/apikeys/shodan/bulk_ioc_lookup", json={"bulk_ioc_lookup": True}
        )

        assert response.status_code == 200
        assert _run(_alert_titles(factory)) == ["API key added"]


class TestDeleteApikeyAlert:
    def test_raises_alert_naming_the_provider(self, client, factory):
        client.post("/api/apikeys", json={"name": "shodan", "key": "old-key"})

        response = client.delete("/api/apikeys/shodan")

        assert response.status_code == 200
        titles = _run(_alert_titles(factory))
        assert titles == ["API key added", "API key removed"]

    def test_not_found_does_not_raise_an_alert(self, client, factory):
        response = client.delete("/api/apikeys/does-not-exist")

        assert response.status_code == 404
        assert _run(_alert_titles(factory)) == []
