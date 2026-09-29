from collections.abc import AsyncGenerator
from datetime import UTC, datetime

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from app.core.config.rate_limit_config import limiter
from app.core.dependencies import get_read_db
from app.core.exceptions import AppHTTPException, register_exception_handlers
from app.features.instagram_search.routers import instagram_search_routes
from app.features.instagram_search.schemas.instagram_search_schemas import (
    InstagramHealthResponse,
    InstagramProfileResponse,
)


@pytest.fixture
def client():
    async def _get_read_db() -> AsyncGenerator[None]:
        yield None

    app = FastAPI()
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
    register_exception_handlers(app)
    app.include_router(instagram_search_routes.router)
    app.dependency_overrides[get_read_db] = _get_read_db
    return TestClient(app)


class TestLookupInstagramProfile:
    def test_delegates_to_the_service_and_returns_its_response(self, client, monkeypatch):
        async def fake_perform_profile_lookup(request, db):
            assert request.username == "someuser"
            return InstagramProfileResponse(
                username="someuser",
                followers=100,
                mode="anonymous",
                timestamp=datetime.now(UTC),
            )

        monkeypatch.setattr(
            instagram_search_routes, "perform_profile_lookup", fake_perform_profile_lookup
        )

        response = client.post("/api/instagram-search/profile", json={"username": "@SomeUser"})

        assert response.status_code == 200
        body = response.json()
        assert body["username"] == "someuser"
        assert body["followers"] == 100
        assert body["mode"] == "anonymous"

    def test_not_found_maps_to_the_services_404(self, client, monkeypatch):
        async def fake_perform_profile_lookup(request, db):
            raise AppHTTPException(
                status_code=404,
                detail="Instagram profile 'ghost' does not exist",
                error_code="INSTAGRAM_PROFILE_NOT_FOUND",
            )

        monkeypatch.setattr(
            instagram_search_routes, "perform_profile_lookup", fake_perform_profile_lookup
        )

        response = client.post("/api/instagram-search/profile", json={"username": "ghost"})

        assert response.status_code == 404
        assert response.json()["error_code"] == "INSTAGRAM_PROFILE_NOT_FOUND"

    def test_rejects_an_invalid_username_with_422(self, client):
        response = client.post("/api/instagram-search/profile", json={"username": "bad name!"})
        assert response.status_code == 422

    def test_rejects_a_missing_username_with_422(self, client):
        response = client.post("/api/instagram-search/profile", json={})
        assert response.status_code == 422


class TestInstagramHealth:
    def test_delegates_to_the_health_service(self, client, monkeypatch):
        async def fake_get_health(db):
            return InstagramHealthResponse(
                installed_version="4.15.3",
                latest_pypi_version="4.15.3",
                update_available=False,
                session_configured=True,
            )

        monkeypatch.setattr(instagram_search_routes, "get_health", fake_get_health)

        response = client.get("/api/instagram-search/health")

        assert response.status_code == 200
        body = response.json()
        assert body["installed_version"] == "4.15.3"
        assert body["session_configured"] is True
