"""HTTP-level coverage for external_newsfeed_routes.py. The three read
endpoints (get_news/get_paginated_articles_route/get_recent_articles_route)
run against a real in-memory DB - their crud layer (news_articles_crud.py)
already has its own tests, but article_retrieval_service.py's own wrapper
functions didn't. The fetch/analysis endpoints instead open their own
production-DB session via `managed_session` (independent of any request
lifecycle, per the module's docstring) - each is faked here the same way
tests/core/scans/test_run.py fakes `managed_session`, and the network/LLM
work underneath is mocked too, so nothing here ever touches a real DB or
makes an outbound call."""

import asyncio
import contextlib
from datetime import UTC, datetime

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.core.dependencies import get_db, get_read_db
from app.features.newsfeed.models.newsfeed_models import (
    NewsArticle,
    NewsfeedConfig,
    NewsfeedSettings,
)
from app.features.newsfeed.routers import external_newsfeed_routes


@pytest.fixture
def session_factory(make_session_factory):
    return make_session_factory(
        [NewsfeedSettings.__table__, NewsArticle.__table__, NewsfeedConfig.__table__]
    )


@pytest.fixture
def client(session_factory, monkeypatch):
    @contextlib.asynccontextmanager
    async def fake_managed_session():
        async with session_factory() as db:
            yield db
            await db.commit()

    monkeypatch.setattr(external_newsfeed_routes, "managed_session", fake_managed_session)

    async def _get_read_db():
        async with session_factory() as db:
            yield db
            await db.commit()

    app = FastAPI()
    app.include_router(external_newsfeed_routes.router)
    app.dependency_overrides[get_read_db] = _get_read_db
    app.dependency_overrides[get_db] = _get_read_db
    return TestClient(app)


def _seed_articles(session_factory, count: int) -> None:
    async def _seed():
        async with session_factory() as db:
            db.add(NewsfeedSettings(name="feed-a", url="https://feed-a.example/rss"))
            await db.flush()
            for i in range(count):
                db.add(
                    NewsArticle(
                        feedname="feed-a",
                        icon="default.png",
                        title=f"Article {i}",
                        summary="summary",
                        date=datetime.now(UTC),
                        link=f"https://feed-a.example/article-{i}",
                    )
                )
            await db.commit()

    asyncio.run(_seed())


class TestGetNews:
    def test_returns_articles_within_the_default_retention_window(self, client, session_factory):
        _seed_articles(session_factory, 3)

        response = client.get("/api/newsfeed")

        assert response.status_code == 200
        assert len(response.json()) == 3

    def test_respects_the_limit_param(self, client, session_factory):
        _seed_articles(session_factory, 3)

        response = client.get("/api/newsfeed", params={"limit": 1})

        assert response.status_code == 200
        assert len(response.json()) == 1

    def test_no_articles_returns_an_empty_list(self, client):
        response = client.get("/api/newsfeed")
        assert response.json() == []


class TestGetPaginatedArticles:
    def test_paginates_and_reports_the_total_count(self, client, session_factory):
        _seed_articles(session_factory, 3)

        response = client.get("/api/newsfeed/articles", params={"page": 1, "page_size": 2})

        assert response.status_code == 200
        body = response.json()
        assert body["total_count"] == 3
        assert body["page"] == 1
        assert len(body["articles"]) == 2

    def test_filters_by_tlp(self, client, session_factory):
        _seed_articles(session_factory, 1)

        response = client.get("/api/newsfeed/articles", params={"tlp": "TLP:RED"})

        assert response.status_code == 200
        assert response.json()["total_count"] == 0


class TestGetRecentArticles:
    def test_returns_recent_articles(self, client, session_factory):
        _seed_articles(session_factory, 2)

        response = client.get("/api/newsfeed/articles/recent")

        assert response.status_code == 200
        assert len(response.json()) == 2

    def test_rejects_an_unsupported_time_filter(self, client):
        response = client.get("/api/newsfeed/articles/recent", params={"time_filter": "3weeks"})
        assert response.status_code == 422


class TestFetchNews:
    def test_returns_202_and_schedules_the_background_task(self, client, monkeypatch):
        called = []

        async def fake_fetch(db):
            called.append(True)

        monkeypatch.setattr(external_newsfeed_routes, "fetch_and_store_news", fake_fetch)

        response = client.post("/api/newsfeed/fetch")

        assert response.status_code == 202
        assert response.json() == {"message": "News fetch initiated"}
        assert called == [True]


class TestFetchAndGetNews:
    def test_waits_for_the_fetch_to_complete(self, client, monkeypatch):
        called = []

        async def fake_fetch(db):
            called.append(True)

        monkeypatch.setattr(external_newsfeed_routes, "fetch_and_store_news", fake_fetch)

        response = client.post("/api/newsfeed/fetch_and_get")

        assert response.status_code == 200
        assert response.json() == {"message": "News fetch completed"}
        assert called == [True]


class TestPostAnalyzeTopArticles:
    def test_wraps_the_analysis_results(self, client, monkeypatch):
        async def fake_analyze(db):
            return [{"article_id": 1, "title": "Top story", "analysis": {"verdict": "relevant"}}]

        monkeypatch.setattr(external_newsfeed_routes, "analyze_and_rank_top_articles", fake_analyze)

        response = client.post("/api/newsfeed/analysis/top-articles")

        assert response.status_code == 200
        assert response.json()["articles_analysis"][0]["title"] == "Top story"


class TestGetAnalyzeTopArticlesStream:
    def test_streams_each_yielded_message_as_an_sse_event(self, client, monkeypatch):
        async def fake_stream(db):
            yield "ranking"
            yield "complete"

        monkeypatch.setattr(external_newsfeed_routes, "analyze_top_articles_stream", fake_stream)

        response = client.get("/api/newsfeed/analysis/top-articles/stream")

        assert response.status_code == 200
        assert response.headers["content-type"].startswith("text/event-stream")
        assert "data: ranking" in response.text
        assert "data: complete" in response.text
