"""The /scan, /runs/{id}/cancel, /info, /runs, /runs/{id}, and DELETE /runs/{id}
endpoints. run_scan's own orchestration is ScanRun's concern (covered in
test_phone_search_service.py); this only checks the route wires the request
into it and streams back a response.
"""

import asyncio
from collections.abc import AsyncGenerator
from types import SimpleNamespace

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config.rate_limit_config import limiter
from app.core.dependencies import get_db, get_read_db
from app.core.exceptions import register_exception_handlers
from app.core.scans.run import ScanRun
from app.features.phone_search.models.phone_search_models import PhoneSearch, PhoneSearchResult
from app.features.phone_search.routers import phone_search_routes


@pytest.fixture
def session_factory(make_session_factory):
    return make_session_factory([PhoneSearch.__table__, PhoneSearchResult.__table__])


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
    app.include_router(phone_search_routes.router)
    app.dependency_overrides[get_db] = _get_db
    app.dependency_overrides[get_read_db] = _get_db
    return TestClient(app)


class TestStartScan:
    def test_starts_the_scan_with_the_submitted_number_and_streams_a_response(
        self, client, monkeypatch
    ):
        captured = {}

        async def fake_run_scan(phone_number, queue):
            captured["phone_number"] = phone_number
            queue.put_nowait(None)

        monkeypatch.setattr(phone_search_routes, "run_scan", fake_run_scan)

        response = client.post("/api/phone-search/scan", json={"phone_number": "+15551234567"})

        assert response.status_code == 200
        assert response.headers["content-type"].startswith("text/event-stream")
        assert captured["phone_number"] == "+15551234567"

    def test_rejects_a_non_e164_phone_number(self, client):
        response = client.post("/api/phone-search/scan", json={"phone_number": "not-a-number"})
        assert response.status_code == 422


class TestCancelScan:
    def test_returns_404_when_no_scan_with_that_id_is_running(self, client, monkeypatch):
        async def fake_cancel(search_id):
            return False

        monkeypatch.setattr(ScanRun, "cancel", lambda model, search_id: fake_cancel(search_id))

        response = client.post("/api/phone-search/runs/999/cancel")

        assert response.status_code == 404
        assert response.json()["error_code"] == "PHONE_SEARCH_NOT_RUNNING"

    def test_returns_202_when_cancellation_is_accepted(self, client, monkeypatch):
        async def fake_cancel(search_id):
            return True

        monkeypatch.setattr(ScanRun, "cancel", lambda model, search_id: fake_cancel(search_id))

        response = client.post("/api/phone-search/runs/1/cancel")

        assert response.status_code == 202


class TestReadInfo:
    def test_reports_the_active_checkers(self, client, monkeypatch):
        fake_checkers = [
            SimpleNamespace(PROVIDER_NAME="Amazon"),
            SimpleNamespace(PROVIDER_NAME="Microsoft"),
        ]
        monkeypatch.setattr(phone_search_routes, "get_active_checkers", lambda: fake_checkers)

        response = client.get("/api/phone-search/info")

        assert response.status_code == 200
        body = response.json()
        assert body["provider_count"] == 2
        assert body["providers"] == ["Amazon", "Microsoft"]


class TestReadSearchRuns:
    def test_lists_created_runs(self, client, session_factory):
        async def _seed():
            async with session_factory() as db:
                db.add(PhoneSearch(phone_number="+15551234567", status="completed"))
                await db.commit()

        asyncio.run(_seed())

        response = client.get("/api/phone-search/runs")

        assert response.status_code == 200
        body = response.json()
        assert len(body) == 1
        assert body[0]["phone_number"] == "+15551234567"


class TestReadSearchRun:
    def test_returns_404_for_an_unknown_id(self, client):
        response = client.get("/api/phone-search/runs/999")
        assert response.status_code == 404
        assert response.json()["error_code"] == "PHONE_SEARCH_RUN_NOT_FOUND"

    def test_returns_the_run_with_its_provider_results(self, client, session_factory):
        async def _seed():
            async with session_factory() as db:
                search = PhoneSearch(phone_number="+15551234567", status="completed")
                db.add(search)
                await db.flush()
                db.add(PhoneSearchResult(search_id=search.id, provider_name="Amazon"))
                await db.commit()
                return search.id

        search_id = asyncio.run(_seed())

        response = client.get(f"/api/phone-search/runs/{search_id}")

        assert response.status_code == 200
        body = response.json()
        assert body["phone_number"] == "+15551234567"
        assert body["provider_results"][0]["provider_name"] == "Amazon"


class TestDeleteSearchRun:
    def test_returns_404_for_an_unknown_id(self, client):
        response = client.delete("/api/phone-search/runs/999")
        assert response.status_code == 404

    def test_deletes_an_existing_run(self, client, session_factory):
        async def _seed():
            async with session_factory() as db:
                search = PhoneSearch(phone_number="+15551234567", status="completed")
                db.add(search)
                await db.commit()
                return search.id

        search_id = asyncio.run(_seed())

        response = client.delete(f"/api/phone-search/runs/{search_id}")
        assert response.status_code == 204

        follow_up = client.get(f"/api/phone-search/runs/{search_id}")
        assert follow_up.status_code == 404
