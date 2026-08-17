"""HTTP-level coverage for cti_profile_routes.py, now built on
build_singleton_settings_router with on_error=_map_cti_error - the one adapter
using the new on_error hook to preserve its distinct get/update error mapping
(ValueError -> 400, anything else -> 500, differing error_code per operation).
Also covers that POST /api/settings/cti was removed (unused by the frontend,
functionally duplicated PUT)."""

import asyncio
from collections.abc import AsyncGenerator

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

from app.core.database import Base
from app.core.dependencies import get_db, get_read_db
from app.core.exceptions import AppHTTPException, register_exception_handlers
from app.core.settings.cti_profile.models.cti_profile_models import CTIProfileSettings
from app.core.settings.cti_profile.routers.cti_profile_routes import _map_cti_error, router
from app.core.settings.cti_profile.service import cti_profile_service


@pytest.fixture
def client():
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    session_factory = async_sessionmaker(engine, expire_on_commit=False)

    async def _create_tables():
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all, tables=[CTIProfileSettings.__table__])

    asyncio.run(_create_tables())

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


class TestGetCtiSettings:
    def test_creates_and_returns_defaults(self, client):
        response = client.get("/api/settings/cti")

        assert response.status_code == 200
        assert response.json()["settings"]["profile_name"] == "Default CTI Profile"

    def test_unexpected_error_maps_to_500(self, client, monkeypatch):
        # get_cti_profile_settings reads this crud helper by module-level name at
        # call time, so patching it here (unlike patching the route's own
        # get_service, which the factory already captured into a closure at
        # router-build time) actually reaches the running request.
        async def fake_get_or_create_singleton(db, model, defaults=None):
            raise RuntimeError("boom")

        monkeypatch.setattr(
            cti_profile_service, "get_or_create_singleton", fake_get_or_create_singleton
        )

        response = client.get("/api/settings/cti")

        assert response.status_code == 500
        assert response.json()["error_code"] == "CTI_SETTINGS_RETRIEVE_FAILED"


class TestUpdateCtiSettings:
    def test_updates_settings(self, client):
        response = client.put(
            "/api/settings/cti",
            json={"settings": {"profile_name": "My Profile"}},
        )

        assert response.status_code == 200
        assert response.json()["settings"]["profile_name"] == "My Profile"

    def test_missing_required_field_maps_to_400(self, client):
        response = client.put("/api/settings/cti", json={"settings": {}})

        assert response.status_code == 400
        assert response.json()["error_code"] == "CTI_SETTINGS_INVALID"

    def test_unexpected_error_maps_to_500(self, client, monkeypatch):
        async def fake_update_cti_settings(db, settings):
            raise RuntimeError("boom")

        monkeypatch.setattr(cti_profile_service, "update_cti_settings", fake_update_cti_settings)

        response = client.put("/api/settings/cti", json={"settings": {"profile_name": "x"}})

        assert response.status_code == 500
        assert response.json()["error_code"] == "CTI_SETTINGS_UPDATE_FAILED"


class TestMapCtiError:
    """Direct unit coverage of the on_error hook itself, independent of HTTP wiring."""

    @pytest.mark.parametrize("op", ["get", "update"])
    def test_value_error_maps_to_400_invalid(self, op):
        with pytest.raises(AppHTTPException) as exc_info:
            _map_cti_error(ValueError("bad field"), op)

        assert exc_info.value.status_code == 400
        assert exc_info.value.error_code == "CTI_SETTINGS_INVALID"

    def test_generic_error_maps_to_500_retrieve_failed_for_get(self):
        with pytest.raises(AppHTTPException) as exc_info:
            _map_cti_error(RuntimeError("boom"), "get")

        assert exc_info.value.status_code == 500
        assert exc_info.value.error_code == "CTI_SETTINGS_RETRIEVE_FAILED"

    def test_generic_error_maps_to_500_update_failed_for_update(self):
        with pytest.raises(AppHTTPException) as exc_info:
            _map_cti_error(RuntimeError("boom"), "update")

        assert exc_info.value.status_code == 500
        assert exc_info.value.error_code == "CTI_SETTINGS_UPDATE_FAILED"


class TestPostRemoved:
    def test_post_no_longer_exists(self, client):
        response = client.post("/api/settings/cti", json={"settings": {"profile_name": "x"}})

        assert response.status_code == 405
