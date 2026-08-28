from collections.abc import AsyncGenerator

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_db, get_read_db
from app.core.exceptions import register_exception_handlers
from app.core.settings.modules.models.modules_settings_models import ModuleSettings
from app.core.settings.modules.routers.modules_settings_routes import router


@pytest.fixture
def client(make_session_factory):
    session_factory = make_session_factory([ModuleSettings.__table__])

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


class TestListModuleSettings:
    def test_returns_an_empty_list_initially(self, client):
        response = client.get("/api/settings/modules")
        assert response.status_code == 200
        assert response.json() == []

    def test_returns_created_settings(self, client):
        client.post("/api/settings/modules", json={"name": "newsfeed", "enabled": True})

        response = client.get("/api/settings/modules")

        assert response.status_code == 200
        assert response.json()[0]["name"] == "newsfeed"


class TestGetModuleSetting:
    def test_returns_404_for_a_missing_module(self, client):
        response = client.get("/api/settings/modules/newsfeed")
        assert response.status_code == 404

    def test_returns_the_matching_setting(self, client):
        client.post("/api/settings/modules", json={"name": "newsfeed", "enabled": True})

        response = client.get("/api/settings/modules/newsfeed")

        assert response.status_code == 200
        assert response.json()["enabled"] is True


class TestCreateModuleSetting:
    def test_creates_and_normalizes_the_name(self, client):
        response = client.post("/api/settings/modules", json={"name": "NewsFeed", "enabled": True})

        assert response.status_code == 201
        assert response.json()["name"] == "newsfeed"

    def test_rejects_a_duplicate_module(self, client):
        client.post("/api/settings/modules", json={"name": "newsfeed", "enabled": True})

        response = client.post("/api/settings/modules", json={"name": "newsfeed", "enabled": False})

        assert response.status_code == 409


class TestUpdateModuleSetting:
    def test_updates_the_enabled_status(self, client):
        client.post("/api/settings/modules", json={"name": "newsfeed", "enabled": True})

        response = client.put("/api/settings/modules/newsfeed", json={"enabled": False})

        assert response.status_code == 200
        assert response.json()["enabled"] is False

    def test_returns_404_for_a_missing_module(self, client):
        response = client.put("/api/settings/modules/newsfeed", json={"enabled": False})
        assert response.status_code == 404


class TestUpdateModuleStatus:
    def test_creates_the_setting_when_it_does_not_exist(self, client):
        response = client.patch("/api/settings/modules/newsfeed/status", json={"enabled": True})

        assert response.status_code == 200
        assert response.json() == {"name": "newsfeed", "enabled": True}

    def test_flips_the_status_of_an_existing_setting(self, client):
        client.post("/api/settings/modules", json={"name": "newsfeed", "enabled": True})

        response = client.patch("/api/settings/modules/newsfeed/status", json={"enabled": False})

        assert response.status_code == 200
        assert response.json()["enabled"] is False


class TestDeleteModuleSetting:
    def test_deletes_an_existing_setting(self, client):
        client.post("/api/settings/modules", json={"name": "newsfeed", "enabled": True})

        response = client.delete("/api/settings/modules/newsfeed")

        assert response.status_code == 204
        assert client.get("/api/settings/modules/newsfeed").status_code == 404

    def test_returns_404_for_a_missing_module(self, client):
        response = client.delete("/api/settings/modules/newsfeed")
        assert response.status_code == 404
