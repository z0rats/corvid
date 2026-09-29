"""Route-level contract only - service orchestration is covered in
test_ghunt_profile_service.py/test_ghunt_session_service.py. This checks request validation
(malformed email rejected before the service runs), that AppHTTPException error codes reach the
response body, and that a session value never appears in any response.
"""

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from app.core.config.rate_limit_config import limiter
from app.core.dependencies import get_db, get_read_db
from app.core.exceptions import AppHTTPException, register_exception_handlers
from app.core.settings.api_keys.schemas.api_keys_settings_schemas import ApikeyStateResponse
from app.features.email_search.routers import ghunt_profile_routes
from app.features.email_search.schemas.ghunt_schemas import (
    GhuntHealthResponse,
    GhuntProfileResponse,
)


@pytest.fixture
def client():
    app = FastAPI()
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
    register_exception_handlers(app)
    app.include_router(ghunt_profile_routes.router)
    app.dependency_overrides[get_read_db] = lambda: None
    app.dependency_overrides[get_db] = lambda: None
    return TestClient(app)


class TestLookupGhuntProfile:
    def test_rejects_a_malformed_email_before_calling_the_service(self, client, monkeypatch):
        async def fake_run(db, email):
            raise AssertionError("service should not run for an invalid email")

        monkeypatch.setattr(ghunt_profile_routes, "run_ghunt_profile", fake_run)

        response = client.post("/api/email-search/ghunt-profile", json={"email": "not-an-email"})

        assert response.status_code == 422

    def test_returns_the_service_result_for_a_valid_email(self, client, monkeypatch):
        async def fake_run(db, email):
            assert email == "target@gmail.com"
            return GhuntProfileResponse(gaia_id="123", email=email)

        monkeypatch.setattr(ghunt_profile_routes, "run_ghunt_profile", fake_run)

        response = client.post(
            "/api/email-search/ghunt-profile", json={"email": "target@gmail.com"}
        )

        assert response.status_code == 200
        assert response.json()["gaia_id"] == "123"

    def test_app_http_exception_error_code_reaches_the_response_body(self, client, monkeypatch):
        async def fake_run(db, email):
            raise AppHTTPException(
                status_code=409, detail="No session configured", error_code="GHUNT_SESSION_MISSING"
            )

        monkeypatch.setattr(ghunt_profile_routes, "run_ghunt_profile", fake_run)

        response = client.post(
            "/api/email-search/ghunt-profile", json={"email": "target@gmail.com"}
        )

        assert response.status_code == 409
        assert response.json()["error_code"] == "GHUNT_SESSION_MISSING"


class TestReadGhuntHealth:
    def test_returns_the_service_result(self, client, monkeypatch):
        async def fake_health(db):
            return GhuntHealthResponse(
                installed=True, version="2.3.4", latest_version=None, session_configured=False
            )

        monkeypatch.setattr(ghunt_profile_routes, "get_ghunt_health", fake_health)

        response = client.get("/api/email-search/ghunt-profile/health")

        assert response.status_code == 200
        body = response.json()
        assert body["installed"] is True
        assert body["session_configured"] is False


class TestSaveSession:
    def test_invalid_session_returns_400_without_leaking_the_value_back(self, client, monkeypatch):
        async def fake_save(db, value):
            raise AppHTTPException(
                status_code=400,
                detail="Not a valid GHunt session",
                error_code="GHUNT_SESSION_INVALID",
            )

        monkeypatch.setattr(ghunt_profile_routes, "save_ghunt_session", fake_save)

        response = client.put("/api/email-search/ghunt-profile/session", json={"value": "garbage"})

        assert response.status_code == 400
        assert "garbage" not in response.text

    def test_valid_session_is_saved_and_never_echoed_back(self, client, monkeypatch):
        session_value = "c29tZS1zZXNzaW9uLXZhbHVl"

        async def fake_save(db, value):
            assert value == session_value
            return ApikeyStateResponse(name="ghunt_session", is_active=True)

        monkeypatch.setattr(ghunt_profile_routes, "save_ghunt_session", fake_save)

        response = client.put(
            "/api/email-search/ghunt-profile/session",
            json={"value": session_value},
        )

        assert response.status_code == 200
        body = response.json()
        assert body == {"name": "ghunt_session", "is_active": True}
        assert session_value not in response.text
