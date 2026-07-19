import asyncio
from datetime import datetime, timedelta, timezone

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

from app.core.config.rate_limit_config import limiter
from app.core.database import Base
from app.core.dependencies import get_read_db
from app.features.ioc_tools.ioc_lookup.single_lookup.routers.unified_routes import router as ioc_lookup_router
from app.features.newsfeed.crud.news_articles_crud import get_articles_mentioning_ioc
from app.features.newsfeed.models.newsfeed_models import NewsArticle, NewsfeedSettings


def _run(coro):
    return asyncio.run(coro)


@pytest.fixture
def engine():
    """An isolated in-memory SQLite engine holding only the newsfeed tables this
    crud query touches — cheaper than spinning up the full app schema."""
    return create_async_engine(
        "sqlite+aiosqlite:///:memory:", connect_args={"check_same_thread": False}, poolclass=StaticPool,
    )


@pytest.fixture
def session_factory(engine):
    async def _create_tables():
        async with engine.begin() as conn:
            await conn.run_sync(
                Base.metadata.create_all, tables=[NewsfeedSettings.__table__, NewsArticle.__table__],
            )

    _run(_create_tables())
    return async_sessionmaker(engine, expire_on_commit=False)


async def _seed_article(session_factory, *, link, iocs, days_ago=0, title="Test Article"):
    async with session_factory() as db:
        existing = await db.get(NewsfeedSettings, "feed1")
        if existing is None:
            db.add(NewsfeedSettings(name="feed1", url="https://example.com/feed"))
            await db.flush()
        db.add(NewsArticle(
            feedname="feed1",
            icon="default.png",
            title=title,
            summary="summary",
            date=datetime.now(timezone.utc) - timedelta(days=days_ago),
            link=link,
            iocs=iocs,
        ))
        await db.commit()


class TestGetArticlesMentioningIoc:
    def test_finds_article_by_exact_ioc_value(self, session_factory):
        _run(_seed_article(
            session_factory, link="https://news.example/a", iocs={"ips": ["1.2.3.4"]},
        ))

        async def _query():
            async with session_factory() as db:
                return await get_articles_mentioning_ioc(db, "1.2.3.4")

        articles = _run(_query())

        assert len(articles) == 1
        assert articles[0].link == "https://news.example/a"

    def test_match_is_case_insensitive(self, session_factory):
        _run(_seed_article(
            session_factory, link="https://news.example/b", iocs={"sha256": ["ABCDEF0123456789"]},
        ))

        async def _query():
            async with session_factory() as db:
                return await get_articles_mentioning_ioc(db, "abcdef0123456789")

        assert len(_run(_query())) == 1

    def test_no_match_for_unrelated_ioc(self, session_factory):
        _run(_seed_article(
            session_factory, link="https://news.example/c", iocs={"ips": ["1.2.3.4"]},
        ))

        async def _query():
            async with session_factory() as db:
                return await get_articles_mentioning_ioc(db, "9.9.9.9")

        assert _run(_query()) == []

    def test_does_not_match_substring_of_a_longer_value(self, session_factory):
        """"1.2.3.4" must not match an article that only mentions "111.2.3.4"."""
        _run(_seed_article(
            session_factory, link="https://news.example/d", iocs={"ips": ["111.2.3.4"]},
        ))

        async def _query():
            async with session_factory() as db:
                return await get_articles_mentioning_ioc(db, "1.2.3.4")

        assert _run(_query()) == []

    def test_ignores_articles_with_no_extracted_iocs(self, session_factory):
        _run(_seed_article(session_factory, link="https://news.example/e", iocs=None))

        async def _query():
            async with session_factory() as db:
                return await get_articles_mentioning_ioc(db, "1.2.3.4")

        assert _run(_query()) == []

    def test_orders_most_recent_first_and_respects_limit(self, session_factory):
        _run(_seed_article(session_factory, link="https://news.example/older", iocs={"ips": ["5.5.5.5"]}, days_ago=5))
        _run(_seed_article(session_factory, link="https://news.example/newer", iocs={"ips": ["5.5.5.5"]}, days_ago=1))

        async def _query():
            async with session_factory() as db:
                return await get_articles_mentioning_ioc(db, "5.5.5.5", limit=1)

        articles = _run(_query())

        assert len(articles) == 1
        assert articles[0].link == "https://news.example/newer"

    def test_escapes_like_wildcards_in_ioc_value(self, session_factory):
        """A literal "%" or "_" in the searched value must not act as a SQL LIKE wildcard."""
        _run(_seed_article(session_factory, link="https://news.example/f", iocs={"emails": ["a_b@example.com"]}))

        async def _query():
            async with session_factory() as db:
                return await get_articles_mentioning_ioc(db, "aXb@example.com")

        assert _run(_query()) == []


@pytest.fixture
def client(session_factory):
    """A minimal FastAPI app exposing only the ioc_lookup single-lookup router,
    with the read-DB dependency overridden to the isolated in-memory engine."""
    app = FastAPI()
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
    app.include_router(ioc_lookup_router)

    async def _override_get_read_db():
        async with session_factory() as db:
            yield db

    app.dependency_overrides[get_read_db] = _override_get_read_db
    return TestClient(app)


class TestNewsfeedMentionsEndpoint:
    def test_returns_matching_articles(self, client, session_factory):
        _run(_seed_article(session_factory, link="https://news.example/g", iocs={"ips": ["8.8.8.8"]}, title="An article"))

        response = client.get("/api/ioc/newsfeed-mentions", params={"ioc": "8.8.8.8"})

        assert response.status_code == 200
        body = response.json()
        assert body["ioc"] == "8.8.8.8"
        assert len(body["mentions"]) == 1
        assert body["mentions"][0]["title"] == "An article"
        assert body["mentions"][0]["link"] == "https://news.example/g"

    def test_returns_empty_mentions_when_no_match(self, client):
        response = client.get("/api/ioc/newsfeed-mentions", params={"ioc": "no-such-ioc.example"})

        assert response.status_code == 200
        assert response.json()["mentions"] == []
