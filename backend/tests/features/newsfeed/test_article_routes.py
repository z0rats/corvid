"""HTTP-level coverage for article_routes.py, exercised against a real in-memory
DB rather than a mocked service - article_retrieval_service.py had no tests of
its own either, so this covers both layers at once."""

import asyncio
from collections.abc import AsyncGenerator
from datetime import UTC, datetime

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_db, get_read_db
from app.core.exceptions import register_exception_handlers
from app.features.newsfeed.models.newsfeed_models import NewsArticle, NewsfeedSettings
from app.features.newsfeed.routers import article_routes


@pytest.fixture
def session_factory(make_session_factory):
    return make_session_factory([NewsfeedSettings.__table__, NewsArticle.__table__])


@pytest.fixture
def client(session_factory):
    async def _get_db() -> AsyncGenerator[AsyncSession]:
        async with session_factory() as db:
            yield db
            await db.commit()

    app = FastAPI()
    register_exception_handlers(app)
    app.include_router(article_routes.router)
    app.dependency_overrides[get_db] = _get_db
    app.dependency_overrides[get_read_db] = _get_db
    return TestClient(app)


def _seed_article(session_factory, **overrides) -> int:
    async def _seed():
        async with session_factory() as db:
            db.add(NewsfeedSettings(name="feed-a", url="https://feed-a.example/rss"))
            await db.flush()
            article = NewsArticle(
                feedname="feed-a",
                icon="default.png",
                title=overrides.pop("title", "Ransomware gang hits a bank"),
                summary=overrides.pop("summary", "summary text"),
                date=overrides.pop("date", datetime(2024, 1, 1, tzinfo=UTC)),
                link=overrides.pop("link", "https://feed-a.example/article-1"),
                **overrides,
            )
            db.add(article)
            await db.commit()
            return article.id

    return asyncio.run(_seed())


class TestGetArticle:
    def test_returns_404_for_an_unknown_id(self, client):
        response = client.get("/api/newsfeed/article/999")
        assert response.status_code == 404
        assert response.json()["error_code"] == "ARTICLE_NOT_FOUND"

    def test_returns_the_matching_article(self, client, session_factory):
        article_id = _seed_article(session_factory, title="Ransomware gang hits a bank")

        response = client.get(f"/api/newsfeed/article/{article_id}")

        assert response.status_code == 200
        assert response.json()["title"] == "Ransomware gang hits a bank"


class TestGetArticlesBulk:
    def test_returns_only_the_articles_that_exist(self, client, session_factory):
        article_id = _seed_article(session_factory)

        response = client.post(
            "/api/newsfeed/articles/bulk", json={"article_ids": [article_id, 999]}
        )

        assert response.status_code == 200
        body = response.json()
        assert len(body) == 1
        assert body[0]["id"] == article_id

    def test_rejects_an_empty_id_list(self, client):
        response = client.post("/api/newsfeed/articles/bulk", json={"article_ids": []})
        assert response.status_code == 422

    def test_rejects_more_than_the_max_ids(self, client):
        response = client.post(
            "/api/newsfeed/articles/bulk", json={"article_ids": list(range(201))}
        )
        assert response.status_code == 422


class TestUpdateArticleEndpoint:
    def test_returns_404_for_an_unknown_id(self, client):
        response = client.patch("/api/newsfeed/article/999", json={"read": True})
        assert response.status_code == 404
        assert response.json()["error_code"] == "ARTICLE_NOT_FOUND"

    def test_updates_the_read_flag(self, client, session_factory):
        article_id = _seed_article(session_factory)

        response = client.patch(f"/api/newsfeed/article/{article_id}", json={"read": True})

        assert response.status_code == 200
        assert response.json()["read"] is True

    def test_updates_the_note_and_tlp(self, client, session_factory):
        article_id = _seed_article(session_factory)

        response = client.patch(
            f"/api/newsfeed/article/{article_id}",
            json={"note": "worth watching", "tlp": "TLP:AMBER"},
        )

        assert response.status_code == 200
        body = response.json()
        assert body["note"] == "worth watching"
        assert body["tlp"] == "TLP:AMBER"

    def test_omitted_fields_leave_existing_values_untouched(self, client, session_factory):
        article_id = _seed_article(session_factory, note="original note")

        response = client.patch(f"/api/newsfeed/article/{article_id}", json={})

        assert response.status_code == 200
        assert response.json()["note"] == "original note"


class TestGetArticleIocs:
    def test_returns_404_for_an_unknown_id(self, client):
        response = client.get("/api/newsfeed/article/999/iocs")
        assert response.status_code == 404
        assert response.json()["error_code"] == "ARTICLE_NOT_FOUND"

    def test_returns_the_extracted_iocs(self, client, session_factory):
        article_id = _seed_article(
            session_factory, iocs={"ips": ["1.2.3.4"], "domains": ["evil.example"]}
        )

        response = client.get(f"/api/newsfeed/article/{article_id}/iocs")

        assert response.status_code == 200
        body = response.json()
        assert body["ips"] == ["1.2.3.4"]
        assert body["domains"] == ["evil.example"]
        assert body["urls"] == []

    def test_an_article_with_no_iocs_returns_all_empty_lists(self, client, session_factory):
        article_id = _seed_article(session_factory)

        response = client.get(f"/api/newsfeed/article/{article_id}/iocs")

        assert response.status_code == 200
        assert all(v == [] for v in response.json().values())
