"""HTTP-level coverage for analytics_routes.py, exercised against a real
in-memory DB - analytics_crud.py (the actual aggregation logic) had no tests
of its own either, so this covers both layers at once."""

import asyncio
from collections.abc import AsyncGenerator
from datetime import UTC, datetime

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_db, get_read_db
from app.features.newsfeed.models.newsfeed_models import (
    NewsArticle,
    NewsfeedSettings,
    TrendsBlacklistEntry,
)
from app.features.newsfeed.routers import analytics_routes


@pytest.fixture
def session_factory(make_session_factory):
    return make_session_factory(
        [NewsfeedSettings.__table__, NewsArticle.__table__, TrendsBlacklistEntry.__table__]
    )


@pytest.fixture
def client(session_factory):
    async def _get_db() -> AsyncGenerator[AsyncSession]:
        async with session_factory() as db:
            yield db
            await db.commit()

    app = FastAPI()
    app.include_router(analytics_routes.router)
    app.dependency_overrides[get_db] = _get_db
    app.dependency_overrides[get_read_db] = _get_db
    return TestClient(app)


def _seed(session_factory, articles: list[dict]) -> None:
    async def _do():
        async with session_factory() as db:
            db.add(NewsfeedSettings(name="feed-a", url="https://feed-a.example/rss"))
            await db.flush()
            for i, overrides in enumerate(articles):
                db.add(
                    NewsArticle(
                        feedname="feed-a",
                        icon="default.png",
                        title=overrides.pop("title", f"Article {i}"),
                        summary="summary",
                        date=overrides.pop("date", datetime.now(UTC)),
                        link=overrides.pop("link", f"https://feed-a.example/article-{i}"),
                        **overrides,
                    )
                )
            await db.commit()

    asyncio.run(_do())


def _blacklist(session_factory, value: str, entry_type: str) -> None:
    async def _do():
        async with session_factory() as db:
            db.add(TrendsBlacklistEntry(value=value, type=entry_type))
            await db.commit()

    asyncio.run(_do())


class TestGetTopIocs:
    def test_counts_and_sorts_by_frequency(self, client, session_factory):
        _seed(
            session_factory,
            [
                {"iocs": {"ips": ["1.2.3.4"]}},
                {"iocs": {"ips": ["1.2.3.4", "5.6.7.8"]}},
            ],
        )

        response = client.get("/api/newsfeed/iocs/top", params={"ioc_type": "ips"})

        assert response.status_code == 200
        body = response.json()
        assert body[0]["value"] == "1.2.3.4"
        assert body[0]["count"] == 2
        assert len(body[0]["article_ids"]) == 2

    def test_excludes_blacklisted_values(self, client, session_factory):
        _seed(session_factory, [{"iocs": {"ips": ["1.2.3.4", "5.6.7.8"]}}])
        _blacklist(session_factory, "1.2.3.4", "ioc")

        response = client.get("/api/newsfeed/iocs/top", params={"ioc_type": "ips"})

        values = [e["value"] for e in response.json()]
        assert "1.2.3.4" not in values
        assert "5.6.7.8" in values

    def test_respects_the_limit_param(self, client, session_factory):
        _seed(session_factory, [{"iocs": {"ips": ["1.1.1.1", "2.2.2.2", "3.3.3.3"]}}])

        response = client.get("/api/newsfeed/iocs/top", params={"ioc_type": "ips", "limit": 1})

        assert len(response.json()) == 1

    def test_maps_hash_ioc_types_to_their_iocs_json_key(self, client, session_factory):
        _seed(session_factory, [{"iocs": {"md5": ["d41d8cd98f00b204e9800998ecf8427e"]}}])

        response = client.get("/api/newsfeed/iocs/top", params={"ioc_type": "md5_hashes"})

        assert response.json()[0]["value"] == "d41d8cd98f00b204e9800998ecf8427e"

    def test_requires_the_ioc_type_param(self, client):
        response = client.get("/api/newsfeed/iocs/top")
        assert response.status_code == 422

    def test_no_matching_articles_returns_an_empty_list(self, client):
        response = client.get("/api/newsfeed/iocs/top", params={"ioc_type": "ips"})
        assert response.json() == []


class TestGetTopCves:
    def test_counts_and_sorts_by_frequency(self, client, session_factory):
        _seed(
            session_factory,
            [
                {"iocs": {"cves": ["CVE-2024-0001"]}},
                {"iocs": {"cves": ["CVE-2024-0001", "CVE-2024-0002"]}},
            ],
        )

        response = client.get("/api/newsfeed/cves/top")

        assert response.status_code == 200
        body = response.json()
        assert body[0]["value"] == "CVE-2024-0001"
        assert body[0]["count"] == 2

    def test_no_matching_articles_returns_an_empty_list(self, client):
        response = client.get("/api/newsfeed/cves/top")
        assert response.json() == []


class TestGetIocDistribution:
    def test_returns_counts_per_type_sorted_descending(self, client, session_factory):
        _seed(
            session_factory,
            [{"iocs": {"ips": ["1.1.1.1", "2.2.2.2"], "domains": ["evil.example"]}}],
        )

        response = client.get("/api/newsfeed/iocs/distribution")

        assert response.status_code == 200
        body = {e["id"]: e["value"] for e in response.json()}
        assert body["ips"] == 2
        assert body["domains"] == 1
        assert response.json()[0]["id"] == "ips"

    def test_no_articles_returns_an_empty_list(self, client):
        response = client.get("/api/newsfeed/iocs/distribution")
        assert response.json() == []


class TestGetTopWords:
    def test_counts_significant_words_across_titles(self, client, session_factory):
        _seed(
            session_factory,
            [
                {"title": "Ransomware gang hits a bank"},
                {"title": "Ransomware group targets hospitals"},
            ],
        )

        response = client.get("/api/newsfeed/words/top")

        assert response.status_code == 200
        words = {e["word"]: e["count"] for e in response.json()}
        assert words["ransomware"] == 2

    def test_excludes_stop_words(self, client, session_factory):
        _seed(session_factory, [{"title": "The bank and the hospital"}])

        response = client.get("/api/newsfeed/words/top")

        words = {e["word"] for e in response.json()}
        assert "the" not in words
        assert "and" not in words

    def test_excludes_blacklisted_words(self, client, session_factory):
        _seed(session_factory, [{"title": "Ransomware gang hits a bank"}])
        _blacklist(session_factory, "ransomware", "word")

        response = client.get("/api/newsfeed/words/top")

        words = {e["word"] for e in response.json()}
        assert "ransomware" not in words

    def test_no_articles_returns_an_empty_list(self, client):
        response = client.get("/api/newsfeed/words/top")
        assert response.json() == []
