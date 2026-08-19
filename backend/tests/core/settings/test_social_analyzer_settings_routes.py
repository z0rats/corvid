"""HTTP-level coverage for social_analyzer_settings_routes.py, now built on
build_singleton_settings_router - a direct-replacement adapter with no hooks."""

from collections.abc import AsyncGenerator

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_db, get_read_db
from app.core.settings.username_search.models.social_analyzer_settings_models import (
    SocialAnalyzerConfig,
)
from app.core.settings.username_search.routers.social_analyzer_settings_routes import router


@pytest.fixture
def client(make_session_factory):
    session_factory = make_session_factory([SocialAnalyzerConfig.__table__])

    async def _get_db() -> AsyncGenerator[AsyncSession]:
        async with session_factory() as db:
            yield db
            await db.commit()

    app = FastAPI()
    app.include_router(router)
    app.dependency_overrides[get_db] = _get_db
    app.dependency_overrides[get_read_db] = _get_db
    return TestClient(app)


class TestGetSocialAnalyzerConfig:
    def test_creates_and_returns_defaults(self, client):
        response = client.get("/api/settings/social-analyzer")

        assert response.status_code == 200
        body = response.json()
        assert body["timeout_seconds"] == 0
        assert body["top_sites_count"] == 0

    def test_omits_unset_optional_fields(self, client):
        response = client.get("/api/settings/social-analyzer")

        assert "latest_pypi_version" not in response.json()


class TestUpdateSocialAnalyzerConfig:
    def test_updates_only_provided_fields(self, client):
        client.get("/api/settings/social-analyzer")

        response = client.put("/api/settings/social-analyzer", json={"timeout_seconds": 5})

        assert response.status_code == 200
        body = response.json()
        assert body["timeout_seconds"] == 5
        assert body["top_sites_count"] == 0

    def test_persists_across_requests(self, client):
        client.put("/api/settings/social-analyzer", json={"top_sites_count": 25})

        response = client.get("/api/settings/social-analyzer")

        assert response.json()["top_sites_count"] == 25
