"""HTTP-level coverage for newsfeed_settings_routes.py, including the
build_singleton_settings_router-based /newsfeed/config sub-router. Exercised
against a real in-memory DB - the newsfeed_settings_crud.py/
newsfeed_config_crud.py layers had no tests of their own either."""

import asyncio
from collections.abc import AsyncGenerator

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_db, get_read_db
from app.core.exceptions import register_exception_handlers
from app.features.newsfeed.models.newsfeed_models import NewsfeedConfig, NewsfeedSettings
from app.features.newsfeed.routers import newsfeed_settings_routes


@pytest.fixture
def session_factory(make_session_factory):
    return make_session_factory([NewsfeedSettings.__table__, NewsfeedConfig.__table__])


@pytest.fixture
def client(session_factory, monkeypatch):
    monkeypatch.setattr(newsfeed_settings_routes, "configure_news_scheduler", lambda *a: None)

    async def _get_db() -> AsyncGenerator[AsyncSession]:
        async with session_factory() as db:
            yield db
            await db.commit()

    app = FastAPI()
    register_exception_handlers(app)
    app.include_router(newsfeed_settings_routes.router)
    app.dependency_overrides[get_db] = _get_db
    app.dependency_overrides[get_read_db] = _get_db
    return TestClient(app)


def _seed_feed(session_factory, **overrides) -> None:
    async def _seed():
        async with session_factory() as db:
            db.add(
                NewsfeedSettings(
                    name=overrides.pop("name", "feed-a"),
                    url=overrides.pop("url", "https://feed-a.example/rss"),
                    **overrides,
                )
            )
            await db.commit()

    asyncio.run(_seed())


class TestReadNewsfeedSettings:
    def test_returns_404_when_none_exist(self, client):
        response = client.get("/api/settings/modules/newsfeed")
        assert response.status_code == 404
        assert response.json()["error_code"] == "NEWSFEED_SETTINGS_NOT_FOUND"

    def test_returns_configured_feeds(self, client, session_factory):
        _seed_feed(session_factory, name="feed-a")

        response = client.get("/api/settings/modules/newsfeed")

        assert response.status_code == 200
        assert response.json()[0]["name"] == "feed-a"

    def test_excludes_soft_deleted_feeds(self, client, session_factory):
        _seed_feed(session_factory, name="feed-a", deleted=True)

        response = client.get("/api/settings/modules/newsfeed")

        assert response.status_code == 404


class TestUpdateSettings:
    def test_updates_an_existing_feed(self, client, session_factory):
        _seed_feed(session_factory, name="feed-a", enabled=True)

        response = client.put(
            "/api/settings/modules/newsfeed",
            json={"name": "feed-a", "url": "https://feed-a.example/rss", "enabled": False},
        )

        assert response.status_code == 200
        assert response.json()["enabled"] is False

    def test_creates_a_new_feed_when_no_active_match_exists(self, client):
        response = client.put(
            "/api/settings/modules/newsfeed",
            json={"name": "feed-b", "url": "https://feed-b.example/rss"},
        )

        assert response.status_code == 200
        assert response.json()["name"] == "feed-b"

    def test_rejects_an_invalid_url(self, client):
        response = client.put(
            "/api/settings/modules/newsfeed", json={"name": "feed-a", "url": "not-a-url"}
        )
        assert response.status_code == 422


class TestUpdateFeedStatus:
    def test_returns_404_for_an_unknown_feed(self, client):
        response = client.patch("/api/settings/modules/newsfeed/absent", json={"enabled": False})
        assert response.status_code == 404
        assert response.json()["error_code"] == "NEWSFEED_NOT_FOUND"

    def test_disables_an_enabled_feed(self, client, session_factory):
        _seed_feed(session_factory, name="feed-a", enabled=True)

        response = client.patch("/api/settings/modules/newsfeed/feed-a", json={"enabled": False})

        assert response.status_code == 200
        assert response.json()["enabled"] is False


class TestRetentionDays:
    def test_get_returns_the_default_when_unset(self, client):
        response = client.get("/api/settings/newsfeed/retention")
        assert response.status_code == 200
        assert response.json() == 0

    def test_update_persists_the_new_value(self, client):
        put_response = client.put("/api/settings/newsfeed/retention", json={"retention_days": 30})

        assert put_response.status_code == 200
        assert put_response.json()["retention_days"] == 30

        get_response = client.get("/api/settings/newsfeed/retention")
        assert get_response.json() == 30

    def test_rejects_a_negative_value(self, client):
        response = client.put("/api/settings/newsfeed/retention", json={"retention_days": -1})
        assert response.status_code == 422


class TestNewsfeedConfigRouter:
    def test_get_returns_defaults_and_creates_the_row(self, client):
        response = client.get("/api/settings/newsfeed/config")

        assert response.status_code == 200
        body = response.json()
        assert body["background_fetch_enabled"] is True
        assert body["fetch_interval_minutes"] == 60

    def test_put_updates_only_the_given_fields(self, client):
        client.get("/api/settings/newsfeed/config")

        response = client.put("/api/settings/newsfeed/config", json={"fetch_interval_minutes": 15})

        assert response.status_code == 200
        body = response.json()
        assert body["fetch_interval_minutes"] == 15
        assert body["background_fetch_enabled"] is True

    def test_put_reconfigures_the_scheduler_with_the_updated_values(self, client, monkeypatch):
        captured = {}
        monkeypatch.setattr(
            newsfeed_settings_routes,
            "configure_news_scheduler",
            lambda enabled, interval: captured.update(enabled=enabled, interval=interval),
        )

        client.put(
            "/api/settings/newsfeed/config",
            json={"background_fetch_enabled": False, "fetch_interval_minutes": 10},
        )

        assert captured == {"enabled": False, "interval": 10}
