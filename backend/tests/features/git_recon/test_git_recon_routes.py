"""HTTP-level coverage for git_recon_routes.py. Scan orchestration itself is
covered in test_run_scan_orchestration.py; this only checks the route wires
requests into it and the history endpoints behave correctly."""

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
from app.core.settings.api_keys.models.api_keys_settings_models import Apikey
from app.features.git_recon.models.git_recon_models import GitReconSearch
from app.features.git_recon.routers import git_recon_routes


@pytest.fixture
def session_factory(make_session_factory):
    return make_session_factory([GitReconSearch.__table__, Apikey.__table__])


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
    app.include_router(git_recon_routes.router)
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

        monkeypatch.setattr(git_recon_routes, "run_scan_task", fake_run_scan_task)

        response = client.post("/api/git-recon/scan", json={"mode": "search", "target": "octocat"})

        assert response.status_code == 200
        assert response.headers["content-type"].startswith("text/event-stream")
        assert captured["mode"] == "search"
        assert captured["target"] == "octocat"
        assert captured["github_token"] is None

    def test_passes_the_configured_github_token_through(self, client, session_factory, monkeypatch):
        import asyncio

        async def _seed():
            async with session_factory() as db:
                db.add(Apikey(name="github_pat", key="ghp_secret", is_active=True))
                await db.commit()

        asyncio.run(_seed())

        captured = {}

        async def fake_run_scan_task(**kwargs):
            captured["github_token"] = kwargs["github_token"]
            kwargs["queue"].put_nowait(None)

        monkeypatch.setattr(git_recon_routes, "run_scan_task", fake_run_scan_task)

        client.post("/api/git-recon/scan", json={"mode": "search", "target": "octocat"})

        assert captured["github_token"] == "ghp_secret"

    def test_rejects_an_empty_target(self, client):
        response = client.post("/api/git-recon/scan", json={"mode": "search", "target": ""})
        assert response.status_code == 422

    def test_rejects_an_invalid_mode(self, client):
        response = client.post("/api/git-recon/scan", json={"mode": "delete", "target": "octocat"})
        assert response.status_code == 422


class TestCancelScanEndpoint:
    def test_returns_404_when_no_scan_with_that_id_is_running(self, client, monkeypatch):
        async def fake_cancel(search_id):
            return False

        monkeypatch.setattr(git_recon_routes, "cancel_scan", fake_cancel)

        response = client.post("/api/git-recon/history/999/cancel")

        assert response.status_code == 404
        assert response.json()["error_code"] == "GIT_RECON_NOT_FOUND"

    def test_returns_202_when_cancellation_is_accepted(self, client, monkeypatch):
        async def fake_cancel(search_id):
            return True

        monkeypatch.setattr(git_recon_routes, "cancel_scan", fake_cancel)

        response = client.post("/api/git-recon/history/1/cancel")

        assert response.status_code == 202


class TestReadSearches:
    def test_lists_past_searches(self, client, session_factory):
        import asyncio

        async def _seed():
            async with session_factory() as db:
                db.add(GitReconSearch(mode="search", target="octocat", status="completed"))
                await db.commit()

        asyncio.run(_seed())

        response = client.get("/api/git-recon/history")

        assert response.status_code == 200
        body = response.json()
        assert len(body) == 1
        assert body[0]["target"] == "octocat"

    def test_returns_an_empty_list_when_none_exist(self, client):
        response = client.get("/api/git-recon/history")
        assert response.json() == []


class TestReadSearch:
    def test_returns_404_for_an_unknown_id(self, client):
        response = client.get("/api/git-recon/history/999")
        assert response.status_code == 404
        assert response.json()["error_code"] == "GIT_RECON_NOT_FOUND"

    def test_returns_the_search_with_its_result(self, client, session_factory):
        import asyncio

        async def _seed():
            async with session_factory() as db:
                search = GitReconSearch(
                    mode="url",
                    target="https://github.com/octocat/hello-world",
                    status="completed",
                    result={"stats": {"repos": 1}},
                )
                db.add(search)
                await db.commit()
                return search.id

        search_id = asyncio.run(_seed())

        response = client.get(f"/api/git-recon/history/{search_id}")

        assert response.status_code == 200
        body = response.json()
        assert body["target"] == "https://github.com/octocat/hello-world"
        assert body["result"]["stats"] == {"repos": 1}


class TestDeleteSearchEndpoint:
    def test_returns_404_for_an_unknown_id(self, client):
        response = client.delete("/api/git-recon/history/999")
        assert response.status_code == 404
        assert response.json()["error_code"] == "GIT_RECON_NOT_FOUND"

    def test_deletes_an_existing_search(self, client, session_factory):
        import asyncio

        async def _seed():
            async with session_factory() as db:
                search = GitReconSearch(mode="search", target="octocat", status="completed")
                db.add(search)
                await db.commit()
                return search.id

        search_id = asyncio.run(_seed())

        response = client.delete(f"/api/git-recon/history/{search_id}")
        assert response.status_code == 204

        follow_up = client.get(f"/api/git-recon/history/{search_id}")
        assert follow_up.status_code == 404
