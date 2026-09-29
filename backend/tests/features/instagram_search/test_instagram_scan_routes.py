"""HTTP-level coverage for instagram_scan_routes.py. Scan orchestration itself
is covered in test_instagram_scan_service.py; this only checks the route wires
requests into it and the history endpoints behave correctly.
"""

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
from app.core.scans.run import ScanRun
from app.features.instagram_search.models.instagram_search_models import InstagramSearch
from app.features.instagram_search.routers import instagram_scan_routes


@pytest.fixture
def session_factory(make_session_factory):
    return make_session_factory([InstagramSearch.__table__])


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
    app.include_router(instagram_scan_routes.router)
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

        monkeypatch.setattr(instagram_scan_routes, "run_scan_task", fake_run_scan_task)

        response = client.post(
            "/api/instagram-search/scan", json={"username": "@SomeUser", "scan_type": "posts"}
        )

        assert response.status_code == 200
        assert response.headers["content-type"].startswith("text/event-stream")
        assert captured["username"] == "someuser"
        assert captured["scan_type"] == "posts"

    def test_rejects_an_empty_username(self, client):
        response = client.post(
            "/api/instagram-search/scan", json={"username": "", "scan_type": "posts"}
        )
        assert response.status_code == 422

    def test_rejects_an_invalid_scan_type(self, client):
        response = client.post(
            "/api/instagram-search/scan", json={"username": "someuser", "scan_type": "bogus"}
        )
        assert response.status_code == 422


class TestCancelScanEndpoint:
    def test_returns_404_when_no_scan_with_that_id_is_running(self, client, monkeypatch):
        async def fake_cancel(search_id):
            return False

        monkeypatch.setattr(ScanRun, "cancel", lambda model, search_id: fake_cancel(search_id))

        response = client.post("/api/instagram-search/history/999/cancel")

        assert response.status_code == 404
        assert response.json()["error_code"] == "INSTAGRAM_SCAN_NOT_FOUND"

    def test_returns_202_when_cancellation_is_accepted(self, client, monkeypatch):
        async def fake_cancel(search_id):
            return True

        monkeypatch.setattr(ScanRun, "cancel", lambda model, search_id: fake_cancel(search_id))

        response = client.post("/api/instagram-search/history/1/cancel")

        assert response.status_code == 202


class TestReadSearches:
    def test_lists_past_searches(self, client, session_factory):
        async def _seed():
            async with session_factory() as db:
                db.add(
                    InstagramSearch(
                        scan_type="followers",
                        username="someuser",
                        mode="anonymous",
                        status="completed",
                    )
                )
                await db.commit()

        asyncio.run(_seed())

        response = client.get("/api/instagram-search/history")

        assert response.status_code == 200
        body = response.json()
        assert len(body) == 1
        assert body[0]["username"] == "someuser"

    def test_returns_an_empty_list_when_none_exist(self, client):
        response = client.get("/api/instagram-search/history")
        assert response.json() == []


class TestReadSearch:
    def test_returns_404_for_an_unknown_id(self, client):
        response = client.get("/api/instagram-search/history/999")
        assert response.status_code == 404
        assert response.json()["error_code"] == "INSTAGRAM_SCAN_NOT_FOUND"

    def test_returns_the_search_with_its_items(self, client, session_factory):
        async def _seed():
            async with session_factory() as db:
                search = InstagramSearch(
                    scan_type="posts",
                    username="someuser",
                    mode="anonymous",
                    status="completed",
                    item_count=1,
                    result=[{"shortcode": "abc"}],
                )
                db.add(search)
                await db.commit()
                return search.id

        search_id = asyncio.run(_seed())

        response = client.get(f"/api/instagram-search/history/{search_id}")

        assert response.status_code == 200
        body = response.json()
        assert body["username"] == "someuser"
        assert body["items"] == [{"shortcode": "abc"}]


class TestDeleteSearchEndpoint:
    def test_returns_404_for_an_unknown_id(self, client):
        response = client.delete("/api/instagram-search/history/999")
        assert response.status_code == 404
        assert response.json()["error_code"] == "INSTAGRAM_SCAN_NOT_FOUND"

    def test_deletes_an_existing_search(self, client, session_factory):
        async def _seed():
            async with session_factory() as db:
                search = InstagramSearch(
                    scan_type="posts", username="someuser", mode="anonymous", status="completed"
                )
                db.add(search)
                await db.commit()
                return search.id

        search_id = asyncio.run(_seed())

        response = client.delete(f"/api/instagram-search/history/{search_id}")
        assert response.status_code == 204

        follow_up = client.get(f"/api/instagram-search/history/{search_id}")
        assert follow_up.status_code == 404
