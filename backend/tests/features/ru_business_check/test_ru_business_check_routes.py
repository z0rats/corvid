"""HTTP-level coverage for ru_business_check_routes.py. Scan orchestration and
report rendering have their own dedicated tests; this only checks the route
wires requests into them and the history/report endpoints behave correctly."""

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
from app.features.ru_business_check.models.ru_business_check_models import RuBusinessCheckSearch
from app.features.ru_business_check.routers import ru_business_check_routes


@pytest.fixture
def session_factory(make_session_factory):
    return make_session_factory([RuBusinessCheckSearch.__table__])


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
    app.include_router(ru_business_check_routes.router)
    app.dependency_overrides[get_db] = _get_db
    app.dependency_overrides[get_read_db] = _get_db
    return TestClient(app)


def _seed_search(session_factory, **overrides) -> int:
    # The real scan service always populates these three as at least `[]`
    # (never leaves them None) before persisting a completed row - SearchDetail's
    # schema assumes that and rejects a raw None, so match it here too.
    overrides.setdefault("checked_sources", [])
    overrides.setdefault("pending_sources", [])
    overrides.setdefault("candidates", [])

    async def _seed():
        async with session_factory() as db:
            search = RuBusinessCheckSearch(
                query=overrides.pop("query", "7712345678"),
                status=overrides.pop("status", "completed"),
                **overrides,
            )
            db.add(search)
            await db.commit()
            return search.id

    return asyncio.run(_seed())


class TestScan:
    def test_starts_the_scan_with_the_submitted_request_and_streams_a_response(
        self, client, monkeypatch
    ):
        captured = {}

        async def fake_run_scan_task(**kwargs):
            captured.update(kwargs)
            kwargs["queue"].put_nowait(None)

        monkeypatch.setattr(ru_business_check_routes, "run_scan_task", fake_run_scan_task)

        response = client.post(
            "/api/ru-business-check/scan",
            json={"query": "7712345678", "website": "example.com"},
        )

        assert response.status_code == 200
        assert response.headers["content-type"].startswith("text/event-stream")
        assert captured["query"] == "7712345678"
        assert captured["website"] == "example.com"
        assert captured["force_refresh"] is False

    def test_rejects_an_empty_query(self, client):
        response = client.post("/api/ru-business-check/scan", json={"query": ""})
        assert response.status_code == 422


class TestCancelScanEndpoint:
    def test_returns_404_when_no_scan_with_that_id_is_running(self, client, monkeypatch):
        async def fake_cancel(search_id):
            return False

        monkeypatch.setattr(ru_business_check_routes, "cancel_scan", fake_cancel)

        response = client.post("/api/ru-business-check/history/999/cancel")

        assert response.status_code == 404
        assert response.json()["error_code"] == "RU_BUSINESS_CHECK_NOT_FOUND"

    def test_returns_202_when_cancellation_is_accepted(self, client, monkeypatch):
        async def fake_cancel(search_id):
            return True

        monkeypatch.setattr(ru_business_check_routes, "cancel_scan", fake_cancel)

        response = client.post("/api/ru-business-check/history/1/cancel")

        assert response.status_code == 202


class TestReadSearches:
    def test_lists_past_searches(self, client, session_factory):
        _seed_search(session_factory, query="7712345678")

        response = client.get("/api/ru-business-check/history")

        assert response.status_code == 200
        body = response.json()
        assert len(body) == 1
        assert body[0]["query"] == "7712345678"

    def test_returns_an_empty_list_when_none_exist(self, client):
        response = client.get("/api/ru-business-check/history")
        assert response.json() == []


class TestReadSearch:
    def test_returns_404_for_an_unknown_id(self, client):
        response = client.get("/api/ru-business-check/history/999")
        assert response.status_code == 404
        assert response.json()["error_code"] == "RU_BUSINESS_CHECK_NOT_FOUND"

    def test_returns_the_search_with_its_flags(self, client, session_factory):
        search_id = _seed_search(
            session_factory,
            query="7712345678",
            flags=[{"code": "X", "severity": "hard", "title": "t", "detail": "d"}],
        )

        response = client.get(f"/api/ru-business-check/history/{search_id}")

        assert response.status_code == 200
        body = response.json()
        assert body["query"] == "7712345678"
        assert body["flags"][0]["code"] == "X"


class TestExportSearchReport:
    def test_returns_404_for_an_unknown_id(self, client):
        response = client.get("/api/ru-business-check/history/999/report")
        assert response.status_code == 404
        assert response.json()["error_code"] == "RU_BUSINESS_CHECK_NOT_FOUND"

    def test_returns_the_generated_report_with_a_content_disposition_header(
        self, client, session_factory, monkeypatch
    ):
        search_id = _seed_search(session_factory)

        def fake_generate_report(search, format):
            assert search.id == search_id
            assert format == "html"
            return b"<html>report</html>", "text/html", "report.html"

        monkeypatch.setattr(
            ru_business_check_routes, "generate_ru_business_check_report", fake_generate_report
        )

        response = client.get(f"/api/ru-business-check/history/{search_id}/report")

        assert response.status_code == 200
        assert response.content == b"<html>report</html>"
        assert 'filename="report.html"' in response.headers["content-disposition"]

    def test_passes_through_the_format_query_param(self, client, session_factory, monkeypatch):
        search_id = _seed_search(session_factory)

        def fake_generate_report(search, format):
            assert format == "pdf"
            return b"%PDF-1.4", "application/pdf", "report.pdf"

        monkeypatch.setattr(
            ru_business_check_routes, "generate_ru_business_check_report", fake_generate_report
        )

        response = client.get(
            f"/api/ru-business-check/history/{search_id}/report", params={"format": "pdf"}
        )

        assert response.status_code == 200
        assert response.headers["content-type"] == "application/pdf"


class TestDeleteSearchEndpoint:
    def test_returns_404_for_an_unknown_id(self, client):
        response = client.delete("/api/ru-business-check/history/999")
        assert response.status_code == 404
        assert response.json()["error_code"] == "RU_BUSINESS_CHECK_NOT_FOUND"

    def test_deletes_an_existing_search(self, client, session_factory):
        search_id = _seed_search(session_factory)

        response = client.delete(f"/api/ru-business-check/history/{search_id}")
        assert response.status_code == 204

        follow_up = client.get(f"/api/ru-business-check/history/{search_id}")
        assert follow_up.status_code == 404
