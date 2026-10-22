"""POST /scan plus the shared history routes. The orchestration itself is covered in
test_telegram_scan_service.py; this checks the request wiring, validation and history shape."""

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
from app.features.telegram_search.models.telegram_search_models import TelegramChannelSearch
from app.features.telegram_search.routers import telegram_search_routes

BASE = "/api/telegram-search"


@pytest.fixture
def session_factory(make_session_factory):
    return make_session_factory([TelegramChannelSearch.__table__])


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
    app.include_router(telegram_search_routes.router)
    app.dependency_overrides[get_db] = _get_db
    app.dependency_overrides[get_read_db] = _get_db
    return TestClient(app)


def _seed(session_factory, **fields):
    defaults = dict(target="@durov", channel="durov", status="completed", max_posts=100)
    defaults.update(fields)

    async def go():
        async with session_factory() as db:
            search = TelegramChannelSearch(**defaults)
            db.add(search)
            await db.commit()
            return search.id

    return asyncio.run(go())


class TestStartScan:
    def test_starts_the_scan_with_the_normalized_channel(self, client, monkeypatch):
        captured = {}

        async def fake_run_scan(scan_request, queue):
            captured.update(
                target=scan_request.target,
                channel=scan_request.channel,
                max_posts=scan_request.max_posts,
            )
            queue.put_nowait(None)

        monkeypatch.setattr(telegram_search_routes, "run_scan", fake_run_scan)

        response = client.post(f"{BASE}/scan", json={"target": " https://t.me/s/Durov "})

        assert response.status_code == 200
        assert response.headers["content-type"].startswith("text/event-stream")
        assert captured == {"target": "https://t.me/s/Durov", "channel": "durov", "max_posts": 100}

    @pytest.mark.parametrize(
        "body",
        [
            {"target": "   "},
            {"target": "ab"},
            {"target": "https://t.me/+invite"},
            {"target": "durov", "max_posts": 0},
            {"target": "durov", "max_posts": 501},
        ],
    )
    def test_rejects_invalid_requests(self, client, body):
        assert client.post(f"{BASE}/scan", json=body).status_code == 422


class TestHistory:
    def test_lists_newest_first_with_summary_fields(self, client, session_factory):
        _seed(
            session_factory,
            channel="old",
            started_at=datetime.datetime(2026, 1, 1, tzinfo=datetime.UTC),
        )
        _seed(
            session_factory,
            channel="durov",
            title="Pavel Durov",
            kind="channel",
            member_count=10_000_000,
            posts_sampled=100,
            started_at=datetime.datetime(2026, 1, 2, tzinfo=datetime.UTC),
        )

        body = client.get(f"{BASE}/history").json()

        assert [s["channel"] for s in body] == ["durov", "old"]
        assert body[0]["title"] == "Pavel Durov"
        assert body[0]["member_count"] == 10_000_000
        assert "result" not in body[0]

    def test_detail_returns_the_result_blob(self, client, session_factory):
        result = {
            "profile": {
                "username": "durov",
                "url": "https://t.me/durov",
                "title": "Pavel Durov",
                "kind": "channel",
                "preview_available": False,
            },
        }
        search_id = _seed(session_factory, result=result)

        response = client.get(f"{BASE}/history/{search_id}")

        assert response.status_code == 200
        assert response.json()["result"]["profile"]["title"] == "Pavel Durov"

    def test_unknown_id_is_404_with_the_feature_error_code(self, client):
        response = client.get(f"{BASE}/history/999")

        assert response.status_code == 404
        assert response.json()["error_code"] == "TELEGRAM_SEARCH_NOT_FOUND"

    def test_delete(self, client, session_factory):
        search_id = _seed(session_factory)

        assert client.delete(f"{BASE}/history/{search_id}").status_code == 204
        assert client.get(f"{BASE}/history/{search_id}").status_code == 404
