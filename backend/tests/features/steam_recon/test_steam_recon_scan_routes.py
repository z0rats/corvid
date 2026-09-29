"""The /scan, /history/{id}/cancel, /history, /history/{id}, and DELETE /history/{id}
endpoints - the counterpart to test_steam_recon_routes.py, which only covers /profile. run_scan's
own orchestration is ScanRun's concern (covered in test_steam_recon_scan_service.py); this only
checks the route wires the request into it and streams back a response.
"""

import asyncio
import datetime
from collections.abc import AsyncGenerator

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config.rate_limit_config import limiter
from app.core.dependencies import get_db, get_read_db
from app.core.exceptions import register_exception_handlers
from app.features.steam_recon.models.steam_recon_models import SteamReconSearch
from app.features.steam_recon.routers import steam_recon_routes


@pytest.fixture
def session_factory(make_session_factory):
    return make_session_factory([SteamReconSearch.__table__])


@pytest.fixture
def client(session_factory):
    async def _get_db() -> AsyncGenerator[AsyncSession]:
        async with session_factory() as db:
            yield db
            await db.commit()

    app = FastAPI()
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
    register_exception_handlers(app)
    app.include_router(steam_recon_routes.router)
    app.dependency_overrides[get_db] = _get_db
    app.dependency_overrides[get_read_db] = _get_db
    return TestClient(app)


def _seed(session_factory, **fields):
    defaults = dict(target="1", status="completed", max_friends=200, include_cs_report=True)
    defaults.update(fields)

    async def go():
        async with session_factory() as db:
            search = SteamReconSearch(**defaults)
            db.add(search)
            await db.commit()
            return search.id

    return asyncio.run(go())


class TestStartScan:
    def test_starts_the_scan_with_the_submitted_request_and_streams_a_response(
        self, client, monkeypatch
    ):
        captured = {}

        async def fake_run_scan(scan_request, queue):
            captured["target"] = scan_request.target
            captured["max_friends"] = scan_request.max_friends
            queue.put_nowait(None)

        monkeypatch.setattr(steam_recon_routes, "run_scan", fake_run_scan)

        response = client.post(
            "/api/steam-recon/scan", json={"target": "robinwalker", "max_friends": 50}
        )

        assert response.status_code == 200
        assert response.headers["content-type"].startswith("text/event-stream")
        assert captured == {"target": "robinwalker", "max_friends": 50}

    def test_rejects_an_empty_target(self, client):
        assert client.post("/api/steam-recon/scan", json={"target": "   "}).status_code == 422

    def test_rejects_a_max_friends_above_the_cap(self, client):
        response = client.post("/api/steam-recon/scan", json={"target": "1", "max_friends": 100000})
        assert response.status_code == 422

    def test_defaults_max_friends_and_include_cs_report(self, client, monkeypatch):
        captured = {}

        async def fake_run_scan(scan_request, queue):
            captured["max_friends"] = scan_request.max_friends
            captured["include_cs_report"] = scan_request.include_cs_report
            queue.put_nowait(None)

        monkeypatch.setattr(steam_recon_routes, "run_scan", fake_run_scan)

        client.post("/api/steam-recon/scan", json={"target": "1"})

        assert captured == {"max_friends": 200, "include_cs_report": True}


class TestCancelScan:
    def test_returns_404_when_no_scan_with_that_id_is_running(self, client, monkeypatch):
        monkeypatch.setattr(steam_recon_routes, "cancel_scan", lambda search_id: _resolved(False))

        response = client.post("/api/steam-recon/history/999/cancel")

        assert response.status_code == 404
        assert response.json()["error_code"] == "STEAM_RECON_NOT_RUNNING"

    def test_returns_202_when_cancellation_is_accepted(self, client, monkeypatch):
        monkeypatch.setattr(steam_recon_routes, "cancel_scan", lambda search_id: _resolved(True))

        response = client.post("/api/steam-recon/history/1/cancel")

        assert response.status_code == 202


async def _resolved(value):
    return value


class TestReadSearches:
    def test_lists_created_searches_most_recent_first(self, client, session_factory):
        # SQLite's CURRENT_TIMESTAMP server_default has only second resolution, so two rows
        # created in the same test can tie on started_at - set it explicitly to make the order
        # unambiguous rather than relying on insertion/rowid order as an accidental tiebreak.
        earlier = datetime.datetime(2026, 1, 1, tzinfo=datetime.UTC)
        later = datetime.datetime(2026, 1, 2, tzinfo=datetime.UTC)
        _seed(session_factory, target="1", persona_name="alice", started_at=earlier)
        _seed(session_factory, target="2", persona_name="bob", started_at=later)

        response = client.get("/api/steam-recon/history")

        assert response.status_code == 200
        body = response.json()
        assert [s["persona_name"] for s in body] == ["bob", "alice"]

    def test_respects_skip_and_limit(self, client, session_factory):
        for i in range(3):
            _seed(session_factory, target=str(i))

        response = client.get("/api/steam-recon/history", params={"skip": 1, "limit": 1})

        assert len(response.json()) == 1


class TestReadSearch:
    def test_returns_404_for_an_unknown_id(self, client):
        response = client.get("/api/steam-recon/history/999")
        assert response.status_code == 404
        assert response.json()["error_code"] == "STEAM_RECON_NOT_FOUND"

    def test_returns_the_search_with_its_result_blob(self, client, session_factory):
        result = {
            "profile": {"steamid64": "1", "visibility": "public"},
            "quick_links": [],
            "close_friends": [],
            "geolocation": {
                "confidence": "low",
                "num_voters": 0,
                "coverage": 0.0,
                "countries": [],
                "states": [],
                "cities": [],
            },
            "cheater_report": None,
        }
        search_id = _seed(session_factory, target="1", steamid64="1", result=result)

        response = client.get(f"/api/steam-recon/history/{search_id}")

        assert response.status_code == 200
        assert response.json()["result"]["profile"]["steamid64"] == "1"


class TestDeleteSearch:
    def test_returns_404_for_an_unknown_id(self, client):
        assert client.delete("/api/steam-recon/history/999").status_code == 404

    def test_deletes_an_existing_search(self, client, session_factory):
        search_id = _seed(session_factory, target="1")

        assert client.delete(f"/api/steam-recon/history/{search_id}").status_code == 204
        assert client.get(f"/api/steam-recon/history/{search_id}").status_code == 404
