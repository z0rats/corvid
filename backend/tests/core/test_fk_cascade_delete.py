"""Proves `ondelete="CASCADE"`/`ondelete="SET NULL"` actually apply at the DB level on SQLite.

docs/database-schema-audit.md finding #1: SQLite ignores `ondelete="CASCADE"`
entirely unless `PRAGMA foreign_keys=ON` is set on every connection, and every
search-history model relies on it (`passive_deletes=True` tells SQLAlchemy "don't
delete children yourself, trust the DB"). `app/core/database.py`'s
`_set_sqlite_pragma` now sets that PRAGMA - this test goes through the real
`create_database_engine()` (not a re-implementation of the PRAGMA) so a future
change that drops it breaks this test, not just production.

Finding #4 (`ai_templates.category_id` previously had no `ondelete` at all) is
covered here too: with FK enforcement on, an unset `ondelete` means SQLite would
raise on delete instead of detaching, which is exactly the behaviour the fix
avoids.
"""
import asyncio
import datetime
from pathlib import Path

import pytest
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import async_sessionmaker

from app.core.config.settings import settings
from app.core.database import Base, create_database_engine
from app.features.email_search.models.email_search_models import MailSearch, MailSearchResult
from app.features.ioc_tools.ioc_lookup.single_lookup.models.lookup_history_models import (
    SingleLookupResult, SingleLookupSearch,
)
from app.features.llm_templates.models.llm_template_models import AITemplate
from app.features.llm_templates.models.template_category_models import TemplateCategory
from app.features.newsfeed.models.newsfeed_models import NewsArticle, NewsfeedSettings
from app.features.reddit_search.models.reddit_search_models import RedditSearch, RedditSearchResult
from app.features.username_search.models.username_search_models import MaigretSearch, MaigretSiteResult


def _run(coro):
    return asyncio.run(coro)


@pytest.fixture
def engine(tmp_path: Path, monkeypatch):
    db_path = tmp_path / "cascade.db"
    monkeypatch.setattr(settings.database, "url", f"sqlite:///{db_path}")
    eng = create_database_engine()
    yield eng
    _run(eng.dispose())


def _session_factory(engine, *tables):
    async def _create_tables():
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all, tables=list(tables))

    _run(_create_tables())
    return async_sessionmaker(engine, expire_on_commit=False)


async def _child_count(session_factory, model, search_id: int) -> int:
    async with session_factory() as db:
        result = await db.execute(select(func.count()).select_from(model).where(model.search_id == search_id))
        return result.scalar_one()


class TestMaigretSearchCascade:
    def test_deleting_search_deletes_site_results(self, engine):
        session_factory = _session_factory(engine, MaigretSearch.__table__, MaigretSiteResult.__table__)

        async def _seed_and_delete():
            async with session_factory() as db:
                search = MaigretSearch(username="alice")
                db.add(search)
                await db.flush()
                db.add_all([
                    MaigretSiteResult(search_id=search.id, site_name="github", url_user="https://github.com/alice"),
                    MaigretSiteResult(search_id=search.id, site_name="reddit", url_user="https://reddit.com/u/alice"),
                ])
                await db.commit()
                search_id = search.id
            async with session_factory() as db:
                search = await db.get(MaigretSearch, search_id)
                await db.delete(search)
                await db.commit()
            return search_id

        search_id = _run(_seed_and_delete())
        assert _run(_child_count(session_factory, MaigretSiteResult, search_id)) == 0


class TestMailSearchCascade:
    def test_deleting_search_deletes_provider_results(self, engine):
        session_factory = _session_factory(engine, MailSearch.__table__, MailSearchResult.__table__)

        async def _seed_and_delete():
            async with session_factory() as db:
                search = MailSearch(username="alice")
                db.add(search)
                await db.flush()
                db.add_all([
                    MailSearchResult(search_id=search.id, provider_name="gmail", emails=["alice@gmail.com"]),
                    MailSearchResult(search_id=search.id, provider_name="proton", emails=["alice@proton.me"]),
                ])
                await db.commit()
                search_id = search.id
            async with session_factory() as db:
                search = await db.get(MailSearch, search_id)
                await db.delete(search)
                await db.commit()
            return search_id

        search_id = _run(_seed_and_delete())
        assert _run(_child_count(session_factory, MailSearchResult, search_id)) == 0


class TestRedditSearchCascade:
    def test_deleting_search_deletes_search_results(self, engine):
        session_factory = _session_factory(engine, RedditSearch.__table__, RedditSearchResult.__table__)

        async def _seed_and_delete():
            async with session_factory() as db:
                search = RedditSearch(username="alice")
                db.add(search)
                await db.flush()
                db.add_all([
                    RedditSearchResult(
                        search_id=search.id, kind="post", reddit_id="abc123", subreddit="test",
                        permalink="/r/test/abc123", created_utc=1700000000,
                    ),
                    RedditSearchResult(
                        search_id=search.id, kind="comment", reddit_id="def456", subreddit="test",
                        permalink="/r/test/def456", created_utc=1700000100,
                    ),
                ])
                await db.commit()
                search_id = search.id
            async with session_factory() as db:
                search = await db.get(RedditSearch, search_id)
                await db.delete(search)
                await db.commit()
            return search_id

        search_id = _run(_seed_and_delete())
        assert _run(_child_count(session_factory, RedditSearchResult, search_id)) == 0


class TestSingleLookupCascade:
    def test_deleting_search_deletes_results(self, engine):
        session_factory = _session_factory(engine, SingleLookupSearch.__table__, SingleLookupResult.__table__)

        async def _seed_and_delete():
            async with session_factory() as db:
                search = SingleLookupSearch(ioc="1.2.3.4", ioc_type="ip")
                db.add(search)
                await db.flush()
                db.add_all([
                    SingleLookupResult(
                        search_id=search.id, service_key="shodan", service_name="Shodan",
                        status="found", summary="test", tlp="TLP:CLEAR",
                    ),
                    SingleLookupResult(
                        search_id=search.id, service_key="virustotal", service_name="VirusTotal",
                        status="found", summary="test", tlp="TLP:CLEAR",
                    ),
                ])
                await db.commit()
                search_id = search.id
            async with session_factory() as db:
                search = await db.get(SingleLookupSearch, search_id)
                await db.delete(search)
                await db.commit()
            return search_id

        search_id = _run(_seed_and_delete())
        assert _run(_child_count(session_factory, SingleLookupResult, search_id)) == 0


class TestNewsfeedCascade:
    def test_deleting_feed_deletes_articles(self, engine):
        session_factory = _session_factory(engine, NewsfeedSettings.__table__, NewsArticle.__table__)

        async def _seed_and_delete():
            async with session_factory() as db:
                feed = NewsfeedSettings(name="test-feed", url="https://example.com/rss")
                db.add(feed)
                await db.flush()
                db.add_all([
                    NewsArticle(
                        feedname=feed.name, icon="default.png", title="Article 1", summary="s1",
                        date=datetime.datetime.now(datetime.timezone.utc),
                        link="https://example.com/1",
                    ),
                    NewsArticle(
                        feedname=feed.name, icon="default.png", title="Article 2", summary="s2",
                        date=datetime.datetime.now(datetime.timezone.utc),
                        link="https://example.com/2",
                    ),
                ])
                await db.commit()
                feed_name = feed.name
            async with session_factory() as db:
                feed = await db.get(NewsfeedSettings, feed_name)
                await db.delete(feed)
                await db.commit()
            return feed_name

        feed_name = _run(_seed_and_delete())

        async def _count():
            async with session_factory() as db:
                result = await db.execute(
                    select(func.count()).select_from(NewsArticle).where(NewsArticle.feedname == feed_name)
                )
                return result.scalar_one()

        assert _run(_count()) == 0


class TestAITemplateCategoryDeleteSetsNull:
    def test_deleting_category_detaches_templates_instead_of_blocking(self, engine):
        session_factory = _session_factory(engine, TemplateCategory.__table__, AITemplate.__table__)

        async def _seed_and_delete():
            async with session_factory() as db:
                category = TemplateCategory(name="Recon")
                db.add(category)
                await db.flush()
                template = AITemplate(
                    title="Template", ai_agent_role="role", ai_agent_task="task",
                    payload_fields=[], is_public=False, category_id=category.id,
                )
                db.add(template)
                await db.commit()
                category_id, template_id = category.id, template.id
            async with session_factory() as db:
                category = await db.get(TemplateCategory, category_id)
                await db.delete(category)
                await db.commit()
            return template_id

        template_id = _run(_seed_and_delete())

        async def _category_id():
            async with session_factory() as db:
                template = await db.get(AITemplate, template_id)
                return template.category_id

        assert _run(_category_id()) is None
