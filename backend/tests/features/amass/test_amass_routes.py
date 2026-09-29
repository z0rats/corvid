"""HTTP-level coverage for amass_routes.py. Scan orchestration itself is
covered in test_amass_service.py; this only checks the route wires requests
into it and the history endpoints behave correctly."""

import asyncio
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
from app.features.amass.models.amass_models import AmassSearch
from app.features.amass.routers import amass_routes


@pytest.fixture
def session_factory(make_session_factory):
    return make_session_factory([AmassSearch.__table__])


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
    app.include_router(amass_routes.router)
    app.dependency_overrides[get_db] = _get_db
    app.dependency_overrides[get_read_db] = _get_db
    return TestClient(app)


class TestScan:
    def test_starts_the_scan_with_the_submitted_request_and_streams_a_response(
        self, client, monkeypatch
    ):
        captured = {}

        async def fake_run_scan_task(**kwargs):
            captured.update(kwargs)
            kwargs["queue"].put_nowait(None)

        monkeypatch.setattr(amass_routes, "run_scan_task", fake_run_scan_task)

        response = client.post("/api/amass/scan", json={"domain": "example.com"})

        assert response.status_code == 200
        assert response.headers["content-type"].startswith("text/event-stream")
        assert captured["domain"] == "example.com"
        assert captured["brute_force"] is False

    def test_passes_through_brute_force(self, client, monkeypatch):
        captured = {}

        async def fake_run_scan_task(**kwargs):
            captured.update(kwargs)
            kwargs["queue"].put_nowait(None)

        monkeypatch.setattr(amass_routes, "run_scan_task", fake_run_scan_task)

        client.post("/api/amass/scan", json={"domain": "example.com", "brute_force": True})

        assert captured["brute_force"] is True

    def test_rejects_an_empty_domain(self, client):
        response = client.post("/api/amass/scan", json={"domain": ""})
        assert response.status_code == 422

    def test_rejects_a_wildcard_domain(self, client):
        response = client.post("/api/amass/scan", json={"domain": "example-*"})
        assert response.status_code == 422


class TestCancelScanEndpoint:
    def test_returns_404_when_no_scan_with_that_id_is_running(self, client, monkeypatch):
        async def fake_cancel(search_id):
            return False

        monkeypatch.setattr(amass_routes, "cancel_scan", fake_cancel)

        response = client.post("/api/amass/history/999/cancel")

        assert response.status_code == 404
        assert response.json()["error_code"] == "AMASS_NOT_FOUND"

    def test_returns_202_when_cancellation_is_accepted(self, client, monkeypatch):
        async def fake_cancel(search_id):
            return True

        monkeypatch.setattr(amass_routes, "cancel_scan", fake_cancel)

        response = client.post("/api/amass/history/1/cancel")

        assert response.status_code == 202


class TestReadSearches:
    def test_lists_past_searches(self, client, session_factory):
        async def _seed():
            async with session_factory() as db:
                db.add(AmassSearch(domain="example.com", status="completed", hosts_found=3))
                await db.commit()

        asyncio.run(_seed())

        response = client.get("/api/amass/history")

        assert response.status_code == 200
        body = response.json()
        assert len(body) == 1
        assert body[0]["domain"] == "example.com"
        assert body[0]["hosts_found"] == 3

    def test_returns_an_empty_list_when_none_exist(self, client):
        response = client.get("/api/amass/history")
        assert response.json() == []


class TestReadSearch:
    def test_returns_404_for_an_unknown_id(self, client):
        response = client.get("/api/amass/history/999")
        assert response.status_code == 404
        assert response.json()["error_code"] == "AMASS_NOT_FOUND"

    def test_returns_the_search_with_its_result(self, client, session_factory):
        async def _seed():
            async with session_factory() as db:
                search = AmassSearch(
                    domain="example.com",
                    status="completed",
                    hosts_found=1,
                    result={"hosts": [{"hostname": "www.example.com", "ip": "1.2.3.4"}]},
                )
                db.add(search)
                await db.commit()
                return search.id

        search_id = asyncio.run(_seed())

        response = client.get(f"/api/amass/history/{search_id}")

        assert response.status_code == 200
        body = response.json()
        assert body["domain"] == "example.com"
        assert body["result"]["hosts"] == [{"hostname": "www.example.com", "ip": "1.2.3.4"}]


class TestDeleteSearchEndpoint:
    def test_returns_404_for_an_unknown_id(self, client):
        response = client.delete("/api/amass/history/999")
        assert response.status_code == 404
        assert response.json()["error_code"] == "AMASS_NOT_FOUND"

    def test_deletes_an_existing_search(self, client, session_factory):
        async def _seed():
            async with session_factory() as db:
                search = AmassSearch(domain="example.com", status="completed")
                db.add(search)
                await db.commit()
                return search.id

        search_id = asyncio.run(_seed())

        response = client.delete(f"/api/amass/history/{search_id}")
        assert response.status_code == 204

        follow_up = client.get(f"/api/amass/history/{search_id}")
        assert follow_up.status_code == 404


class TestHealth:
    def test_reports_installed_status_and_version(self, client, monkeypatch):
        monkeypatch.setattr(amass_routes, "get_amass_version", lambda: "v5.1.1")

        response = client.get("/api/amass/health")

        assert response.status_code == 200
        body = response.json()
        assert body["amass_installed"] is True
        assert body["amass_version"] == "v5.1.1"
