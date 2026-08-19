"""The /scan, /runs/{id}/cancel, /runs, /runs/{id}, and DELETE /runs/{id}
endpoints - the counterpart to test_email_search_routes.py, which only covers
the two PyPI-update-check endpoints. run_scan's own orchestration is ScanRun's
concern (covered in test_email_search_service.py); this only checks the route
wires the request into it and streams back a response.
"""

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
from app.features.email_search.models.email_search_models import MailSearch, MailSearchResult
from app.features.email_search.routers import email_search_routes


@pytest.fixture
def session_factory(make_session_factory):
    return make_session_factory([MailSearch.__table__, MailSearchResult.__table__])


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
    app.include_router(email_search_routes.router)
    app.dependency_overrides[get_db] = _get_db
    app.dependency_overrides[get_read_db] = _get_db
    return TestClient(app)


class TestStartScan:
    def test_starts_the_scan_with_the_submitted_username_and_streams_a_response(
        self, client, monkeypatch
    ):
        captured = {}

        async def fake_run_scan(username, queue):
            captured["username"] = username
            queue.put_nowait(None)

        monkeypatch.setattr(email_search_routes, "run_scan", fake_run_scan)

        response = client.post("/api/email-search/scan", json={"username": "alice"})

        assert response.status_code == 200
        assert response.headers["content-type"].startswith("text/event-stream")
        assert captured["username"] == "alice"

    def test_rejects_an_empty_username(self, client):
        response = client.post("/api/email-search/scan", json={"username": "   "})
        assert response.status_code == 422

    def test_strips_the_domain_from_an_email_shaped_input(self, client, monkeypatch):
        captured = {}

        async def fake_run_scan(username, queue):
            captured["username"] = username
            queue.put_nowait(None)

        monkeypatch.setattr(email_search_routes, "run_scan", fake_run_scan)

        client.post("/api/email-search/scan", json={"username": "alice@example.com"})

        assert captured["username"] == "alice"


class TestCancelScan:
    def test_returns_404_when_no_scan_with_that_id_is_running(self, client, monkeypatch):
        async def fake_cancel(search_id):
            return False

        monkeypatch.setattr(email_search_routes, "cancel_scan", fake_cancel)

        response = client.post("/api/email-search/runs/999/cancel")

        assert response.status_code == 404
        assert response.json()["error_code"] == "EMAIL_SEARCH_NOT_RUNNING"

    def test_returns_202_when_cancellation_is_accepted(self, client, monkeypatch):
        async def fake_cancel(search_id):
            return True

        monkeypatch.setattr(email_search_routes, "cancel_scan", fake_cancel)

        response = client.post("/api/email-search/runs/1/cancel")

        assert response.status_code == 202


class TestReadSearchRuns:
    def test_lists_created_runs(self, client, session_factory):
        import asyncio

        async def _seed():
            async with session_factory() as db:
                db.add(MailSearch(username="alice", status="completed"))
                await db.commit()

        asyncio.run(_seed())

        response = client.get("/api/email-search/runs")

        assert response.status_code == 200
        body = response.json()
        assert len(body) == 1
        assert body[0]["username"] == "alice"


class TestReadSearchRun:
    def test_returns_404_for_an_unknown_id(self, client):
        response = client.get("/api/email-search/runs/999")
        assert response.status_code == 404
        assert response.json()["error_code"] == "EMAIL_SEARCH_RUN_NOT_FOUND"

    def test_returns_the_run_with_its_provider_results(self, client, session_factory):
        import asyncio

        async def _seed():
            async with session_factory() as db:
                search = MailSearch(username="alice", status="completed")
                db.add(search)
                await db.flush()
                db.add(
                    MailSearchResult(
                        search_id=search.id, provider_name="gmail", emails=["a@gmail.com"]
                    )
                )
                await db.commit()
                return search.id

        search_id = asyncio.run(_seed())

        response = client.get(f"/api/email-search/runs/{search_id}")

        assert response.status_code == 200
        body = response.json()
        assert body["username"] == "alice"
        assert body["provider_results"][0]["provider_name"] == "gmail"


class TestDeleteSearchRun:
    def test_returns_404_for_an_unknown_id(self, client):
        response = client.delete("/api/email-search/runs/999")
        assert response.status_code == 404

    def test_deletes_an_existing_run(self, client, session_factory):
        import asyncio

        async def _seed():
            async with session_factory() as db:
                search = MailSearch(username="alice", status="completed")
                db.add(search)
                await db.commit()
                return search.id

        search_id = asyncio.run(_seed())

        response = client.delete(f"/api/email-search/runs/{search_id}")
        assert response.status_code == 204

        follow_up = client.get(f"/api/email-search/runs/{search_id}")
        assert follow_up.status_code == 404
