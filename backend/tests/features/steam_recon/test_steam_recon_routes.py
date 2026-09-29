from collections.abc import AsyncGenerator

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from app.core.config.rate_limit_config import limiter
from app.core.dependencies import get_read_db
from app.core.exceptions import AppHTTPException, register_exception_handlers
from app.features.steam_recon.routers import steam_recon_routes
from app.features.steam_recon.schemas.steam_recon_schemas import ProfileResponse, SteamProfile


@pytest.fixture
def client():
    async def _get_read_db() -> AsyncGenerator[None]:
        yield None

    app = FastAPI()
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
    register_exception_handlers(app)
    app.include_router(steam_recon_routes.router)
    app.dependency_overrides[get_read_db] = _get_read_db
    return TestClient(app)


def test_profile_delegates_to_the_service_and_returns_its_response(client, monkeypatch):
    async def fake_lookup(request, db):
        assert request.target == "robinwalker"
        return ProfileResponse(
            profile=SteamProfile(steamid64="76561197960435530", persona_name="Robin"),
            quick_links=[],
        )

    monkeypatch.setattr(steam_recon_routes, "perform_profile_lookup", fake_lookup)

    response = client.post("/api/steam-recon/profile", json={"target": "  robinwalker  "})

    assert response.status_code == 200
    assert response.json()["profile"]["persona_name"] == "Robin"


def test_service_errors_keep_their_status_and_error_code(client, monkeypatch):
    async def fake_lookup(request, db):
        raise AppHTTPException(
            status_code=400, detail="Not a recognized", error_code="STEAM_INVALID_TARGET"
        )

    monkeypatch.setattr(steam_recon_routes, "perform_profile_lookup", fake_lookup)

    response = client.post("/api/steam-recon/profile", json={"target": "???"})

    assert response.status_code == 400
    assert response.json()["error_code"] == "STEAM_INVALID_TARGET"


@pytest.mark.parametrize("body", [{}, {"target": ""}, {"target": "   "}, {"target": "x" * 513}])
def test_invalid_request_bodies_are_rejected(client, body):
    assert client.post("/api/steam-recon/profile", json=body).status_code == 422
