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
from app.features.reddit_search.models.reddit_search_models import RedditSearch, RedditSearchResult
from app.features.reddit_search.routers import reddit_search_routes


@pytest.fixture
def session_factory(make_session_factory):
    return make_session_factory([RedditSearch.__table__, RedditSearchResult.__table__])


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
    app.include_router(reddit_search_routes.router)
    app.dependency_overrides[get_db] = _get_db
    app.dependency_overrides[get_read_db] = _get_db
    return TestClient(app)


def _fake_fetch_both(items, sources=None, arctic_down=False):
    async def fetch_both(username, kind, **kwargs):
        return items, sources or ["Arctic Shift", "PullPush"], arctic_down

    return fetch_both


class TestScan:
    def test_starts_a_new_search_and_persists_the_first_page(self, client, monkeypatch):
        items = [
            {"id": "a1", "created_utc": 100, "subreddit": "python", "score": 5, "permalink": "/x"}
        ]
        monkeypatch.setattr(reddit_search_routes, "fetch_both", _fake_fetch_both(items))

        response = client.post(
            "/api/reddit-search/scan", json={"username": "spez", "kind": "posts"}
        )

        assert response.status_code == 200
        body = response.json()
        assert body["search_id"]
        assert len(body["items"]) == 1
        assert body["items"][0]["reddit_id"] == "a1"
        assert body["sources"] == ["Arctic Shift", "PullPush"]

    def test_returns_404_when_search_id_does_not_exist(self, client):
        response = client.post(
            "/api/reddit-search/scan",
            json={"username": "spez", "kind": "posts", "search_id": 999},
        )

        assert response.status_code == 404
        assert response.json()["error_code"] == "REDDIT_SEARCH_NOT_FOUND"

    def test_appends_to_an_existing_search_without_creating_a_new_one(self, client, monkeypatch):
        monkeypatch.setattr(reddit_search_routes, "fetch_both", _fake_fetch_both([]))
        first = client.post(
            "/api/reddit-search/scan", json={"username": "spez", "kind": "posts"}
        ).json()

        response = client.post(
            "/api/reddit-search/scan",
            json={"username": "spez", "kind": "posts", "search_id": first["search_id"]},
        )

        assert response.status_code == 200
        assert response.json()["search_id"] == first["search_id"]

    def test_has_more_and_next_cursor_are_set_when_a_full_page_is_returned(
        self, client, monkeypatch
    ):
        from app.features.reddit_search.service.reddit_search_service import LIMIT

        items = [
            {
                "id": f"a{i}",
                "created_utc": 1000 - i,
                "subreddit": "python",
                "score": 1,
                "permalink": "/x",
            }
            for i in range(LIMIT)
        ]
        monkeypatch.setattr(reddit_search_routes, "fetch_both", _fake_fetch_both(items))

        response = client.post(
            "/api/reddit-search/scan", json={"username": "spez", "kind": "posts"}
        )

        body = response.json()
        assert body["has_more"] is True
        assert body["next_cursor"]["before"] == items[-1]["created_utc"]

    def test_has_more_is_false_for_a_partial_page(self, client, monkeypatch):
        items = [
            {"id": "a1", "created_utc": 100, "subreddit": "python", "score": 1, "permalink": "/x"}
        ]
        monkeypatch.setattr(reddit_search_routes, "fetch_both", _fake_fetch_both(items))

        response = client.post(
            "/api/reddit-search/scan", json={"username": "spez", "kind": "posts"}
        )

        body = response.json()
        assert body["has_more"] is False
        assert body["next_cursor"] is None


class TestReadSearches:
    def test_lists_created_searches_with_their_result_count(self, client, monkeypatch):
        items = [
            {"id": "a1", "created_utc": 100, "subreddit": "python", "score": 1, "permalink": "/x"}
        ]
        monkeypatch.setattr(reddit_search_routes, "fetch_both", _fake_fetch_both(items))
        client.post("/api/reddit-search/scan", json={"username": "spez", "kind": "posts"})

        response = client.get("/api/reddit-search/history")

        assert response.status_code == 200
        body = response.json()
        assert len(body) == 1
        assert body[0]["username"] == "spez"
        assert body[0]["result_count"] == 1


class TestReadSearch:
    def test_returns_404_for_an_unknown_id(self, client):
        response = client.get("/api/reddit-search/history/999")
        assert response.status_code == 404

    def test_returns_full_detail_including_results(self, client, monkeypatch):
        items = [
            {"id": "a1", "created_utc": 100, "subreddit": "python", "score": 1, "permalink": "/x"}
        ]
        monkeypatch.setattr(reddit_search_routes, "fetch_both", _fake_fetch_both(items))
        search_id = client.post(
            "/api/reddit-search/scan", json={"username": "spez", "kind": "posts"}
        ).json()["search_id"]

        response = client.get(f"/api/reddit-search/history/{search_id}")

        assert response.status_code == 200
        body = response.json()
        assert body["result_count"] == 1
        assert body["results"][0]["reddit_id"] == "a1"


class TestDeleteSearch:
    def test_returns_404_for_an_unknown_id(self, client):
        response = client.delete("/api/reddit-search/history/999")
        assert response.status_code == 404

    def test_deletes_an_existing_search(self, client, monkeypatch):
        monkeypatch.setattr(reddit_search_routes, "fetch_both", _fake_fetch_both([]))
        search_id = client.post(
            "/api/reddit-search/scan", json={"username": "spez", "kind": "posts"}
        ).json()["search_id"]

        response = client.delete(f"/api/reddit-search/history/{search_id}")
        assert response.status_code == 204

        follow_up = client.get(f"/api/reddit-search/history/{search_id}")
        assert follow_up.status_code == 404
