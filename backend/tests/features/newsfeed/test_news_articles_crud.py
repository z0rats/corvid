from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.features.newsfeed.crud.news_articles_crud import (
    apply_article_filters,
    check_article_exists,
    create_news_article,
    delete_old_news_articles,
    get_all_news_articles,
    get_articles_after_cutoff,
    get_news_article_by_id,
    get_news_articles_by_ids,
    get_news_articles_by_retention,
    get_paginated_articles,
    get_recent_news_articles,
    update_news_article,
)
from app.features.newsfeed.models.newsfeed_models import NewsArticle, NewsfeedSettings
from app.features.newsfeed.schemas.newsfeed_schemas import NewsArticleSchema
from tests.conftest import run as _run

# NB: every test below funnels all its DB work (seeding + the operation under
# test) through a single `_run(...)` call - see `tests/conftest.py`'s
# `async_engine` fixture docstring for why a second `asyncio.run()` in the
# same test would silently corrupt results instead of raising.


@pytest.fixture
def session_factory(make_session_factory):
    return make_session_factory([NewsfeedSettings.__table__, NewsArticle.__table__])


def _article_schema(*, link, days_ago=0, title="Article", tlp="TLP:CLEAR", **overrides):
    now = datetime.now(UTC)
    data = dict(
        feedname="feed1",
        icon="default.png",
        title=title,
        summary="summary",
        date=now - timedelta(days=days_ago),
        link=link,
        fetched_at=now,
        tlp=tlp,
    )
    data.update(overrides)
    return NewsArticleSchema(**data)


async def _ensure_feed(db: AsyncSession) -> None:
    existing = await db.get(NewsfeedSettings, "feed1")
    if existing is None:
        db.add(NewsfeedSettings(name="feed1", url="https://example.com/feed"))
        await db.flush()


async def _seed(db: AsyncSession, **overrides) -> int:
    await _ensure_feed(db)
    article = await create_news_article(db, _article_schema(**overrides))
    await db.flush()
    return article.id


class TestCreateNewsArticle:
    def test_creates_article(self, session_factory):
        async def _scenario():
            async with session_factory() as db:
                article_id = await _seed(db, link="https://news.example/a")
                await db.commit()
                return article_id

        assert _run(_scenario()) is not None

    def test_returns_none_for_duplicate_link(self, session_factory):
        async def _scenario():
            async with session_factory() as db:
                await _ensure_feed(db)
                first = await create_news_article(
                    db, _article_schema(link="https://news.example/dup")
                )
                await db.commit()
                second = await create_news_article(
                    db, _article_schema(link="https://news.example/dup")
                )
                await db.commit()
                return first, second

        first, second = _run(_scenario())
        assert first is not None
        assert second is None

    def test_session_is_still_usable_after_duplicate_rollback(self, session_factory):
        """create_news_article rolls back only its own failed flush, not the
        caller's whole session - a subsequent operation in the same session
        must still work."""

        async def _scenario():
            async with session_factory() as db:
                await _ensure_feed(db)
                await create_news_article(db, _article_schema(link="https://news.example/dup2"))
                await db.commit()
                await create_news_article(db, _article_schema(link="https://news.example/dup2"))
                # session must still accept further work after the rollback
                await create_news_article(db, _article_schema(link="https://news.example/other"))
                await db.commit()
                return await check_article_exists(db, "https://news.example/other")

        assert _run(_scenario()) is True


class TestGetAllNewsArticles:
    def test_returns_created_articles(self, session_factory):
        async def _scenario():
            async with session_factory() as db:
                await _seed(db, link="https://news.example/b")
                await db.commit()
                return await get_all_news_articles(db)

        assert len(_run(_scenario())) == 1

    def test_respects_pagination(self, session_factory):
        async def _scenario():
            async with session_factory() as db:
                for i in range(3):
                    await _seed(db, link=f"https://news.example/page{i}")
                await db.commit()
                return await get_all_news_articles(db, skip=1, limit=1)

        assert len(_run(_scenario())) == 1


class TestGetNewsArticlesByRetention:
    def test_excludes_articles_older_than_retention(self, session_factory):
        async def _scenario():
            async with session_factory() as db:
                await _seed(db, link="https://news.example/old", days_ago=10)
                await _seed(db, link="https://news.example/new", days_ago=1)
                await db.commit()
                return await get_news_articles_by_retention(db, retention_days=5)

        articles = _run(_scenario())
        assert [a.link for a in articles] == ["https://news.example/new"]


class TestGetArticlesAfterCutoff:
    def test_orders_newest_first_and_respects_limit(self, session_factory):
        async def _scenario():
            async with session_factory() as db:
                await _seed(db, link="https://news.example/c-old", days_ago=3)
                await _seed(db, link="https://news.example/c-new", days_ago=1)
                await db.commit()
                cutoff = datetime.now(UTC) - timedelta(days=5)
                return await get_articles_after_cutoff(db, cutoff, limit=1)

        articles = _run(_scenario())
        assert [a.link for a in articles] == ["https://news.example/c-new"]


class TestUpdateNewsArticle:
    def test_updates_only_provided_fields(self, session_factory):
        async def _scenario():
            async with session_factory() as db:
                article_id = await _seed(db, link="https://news.example/upd")
                await db.commit()
                return await update_news_article(db, article_id, note="my note", read=True)

        updated = _run(_scenario())
        assert updated.note == "my note"
        assert updated.read is True
        assert updated.tlp == "TLP:CLEAR"

    def test_returns_none_for_missing_article(self, session_factory):
        async def _scenario():
            async with session_factory() as db:
                return await update_news_article(db, 999, note="x")

        assert _run(_scenario()) is None


class TestDeleteOldNewsArticles:
    def test_deletes_articles_older_than_retention(self, session_factory):
        async def _scenario():
            async with session_factory() as db:
                await _seed(db, link="https://news.example/del-old", days_ago=10)
                await _seed(db, link="https://news.example/del-new", days_ago=1)
                await db.commit()
                await delete_old_news_articles(db, retention_days=5)
                await db.commit()
                return await get_all_news_articles(db)

        remaining = _run(_scenario())
        assert [a.link for a in remaining] == ["https://news.example/del-new"]

    def test_zero_retention_days_means_unlimited_and_deletes_nothing(self, session_factory):
        async def _scenario():
            async with session_factory() as db:
                await _seed(db, link="https://news.example/keep-forever", days_ago=1000)
                await db.commit()
                await delete_old_news_articles(db, retention_days=0)
                await db.commit()
                return await get_all_news_articles(db)

        assert len(_run(_scenario())) == 1


class TestCheckArticleExists:
    def test_true_for_existing_link(self, session_factory):
        async def _scenario():
            async with session_factory() as db:
                await _seed(db, link="https://news.example/exists")
                await db.commit()
                return await check_article_exists(db, "https://news.example/exists")

        assert _run(_scenario()) is True

    def test_false_for_missing_link(self, session_factory):
        async def _scenario():
            async with session_factory() as db:
                return await check_article_exists(db, "https://news.example/missing")

        assert _run(_scenario()) is False


class TestGetNewsArticleById:
    def test_returns_none_for_missing_id(self, session_factory):
        async def _scenario():
            async with session_factory() as db:
                return await get_news_article_by_id(db, 999)

        assert _run(_scenario()) is None


class TestGetNewsArticlesByIds:
    def test_returns_matching_subset(self, session_factory):
        async def _scenario():
            async with session_factory() as db:
                id_a = await _seed(db, link="https://news.example/ids-a")
                id_b = await _seed(db, link="https://news.example/ids-b")
                await _seed(db, link="https://news.example/ids-c")
                await db.commit()
                return await get_news_articles_by_ids(db, [id_a, id_b]), id_a, id_b

        articles, id_a, id_b = _run(_scenario())
        assert {a.id for a in articles} == {id_a, id_b}


class TestGetRecentNewsArticles:
    def test_filters_by_time_range(self, session_factory):
        async def _scenario():
            async with session_factory() as db:
                await _seed(db, link="https://news.example/recent-old", days_ago=10)
                await _seed(db, link="https://news.example/recent-new", days_ago=1)
                await db.commit()
                return await get_recent_news_articles(db, time_filter="5d")

        articles = _run(_scenario())
        assert [a.title for a in articles] == ["Article"]
        assert len(articles) == 1

    def test_falls_back_to_no_filter_for_invalid_time_range(self, session_factory):
        async def _scenario():
            async with session_factory() as db:
                await _seed(db, link="https://news.example/recent-any", days_ago=1000)
                await db.commit()
                return await get_recent_news_articles(db, time_filter="not-a-range")

        assert len(_run(_scenario())) == 1


class TestApplyArticleFilters:
    def test_filters_by_tlp(self, session_factory):
        async def _scenario():
            async with session_factory() as db:
                await _seed(db, link="https://news.example/tlp-red", tlp="TLP:RED")
                await _seed(db, link="https://news.example/tlp-clear", tlp="TLP:CLEAR")
                await db.commit()
                stmt = apply_article_filters(select(NewsArticle), tlp="TLP:RED")
                return (await db.execute(stmt)).scalars().all()

        articles = _run(_scenario())
        assert [a.link for a in articles] == ["https://news.example/tlp-red"]

    def test_filters_by_read_status(self, session_factory):
        async def _scenario():
            async with session_factory() as db:
                id_read = await _seed(db, link="https://news.example/read", read=True)
                await _seed(db, link="https://news.example/unread", read=False)
                await db.commit()
                stmt = apply_article_filters(select(NewsArticle), read=True)
                articles = (await db.execute(stmt)).scalars().all()
                return articles, id_read

        articles, id_read = _run(_scenario())
        assert [a.id for a in articles] == [id_read]

    def test_note_null_filter_excludes_articles_with_notes(self, session_factory):
        async def _scenario():
            async with session_factory() as db:
                await _seed(db, link="https://news.example/has-note", note="a note")
                await _seed(db, link="https://news.example/no-note")
                await db.commit()
                stmt = apply_article_filters(select(NewsArticle), note_null=True)
                return (await db.execute(stmt)).scalars().all()

        articles = _run(_scenario())
        assert [a.link for a in articles] == ["https://news.example/no-note"]

    def test_note_null_false_returns_only_articles_with_notes(self, session_factory):
        async def _scenario():
            async with session_factory() as db:
                await _seed(db, link="https://news.example/has-note2", note="a note")
                await _seed(db, link="https://news.example/no-note2")
                await db.commit()
                stmt = apply_article_filters(select(NewsArticle), note_null=False)
                return (await db.execute(stmt)).scalars().all()

        articles = _run(_scenario())
        assert [a.link for a in articles] == ["https://news.example/has-note2"]

    def test_iocs_null_filter_on_json_dict_column(self, session_factory):
        async def _scenario():
            async with session_factory() as db:
                await _seed(db, link="https://news.example/has-iocs", iocs={"ips": ["1.2.3.4"]})
                await _seed(db, link="https://news.example/no-iocs")
                await db.commit()
                stmt = apply_article_filters(select(NewsArticle), iocs_null=False)
                return (await db.execute(stmt)).scalars().all()

        articles = _run(_scenario())
        assert [a.link for a in articles] == ["https://news.example/has-iocs"]

    def test_matches_null_filter_on_json_list_column(self, session_factory):
        async def _scenario():
            async with session_factory() as db:
                await _seed(db, link="https://news.example/has-matches", matches=["keyword"])
                await _seed(db, link="https://news.example/no-matches")
                await db.commit()
                stmt = apply_article_filters(select(NewsArticle), matches_null=False)
                return (await db.execute(stmt)).scalars().all()

        articles = _run(_scenario())
        assert [a.link for a in articles] == ["https://news.example/has-matches"]

    def test_date_range_filter(self, session_factory):
        async def _scenario():
            async with session_factory() as db:
                await _seed(db, link="https://news.example/range-old", days_ago=20)
                await _seed(db, link="https://news.example/range-new", days_ago=1)
                await db.commit()
                start = (datetime.now(UTC) - timedelta(days=5)).isoformat()
                stmt = apply_article_filters(select(NewsArticle), start_date=start)
                return (await db.execute(stmt)).scalars().all()

        articles = _run(_scenario())
        assert [a.link for a in articles] == ["https://news.example/range-new"]

    def test_invalid_date_string_is_ignored_rather_than_raising(self, session_factory):
        async def _scenario():
            async with session_factory() as db:
                await _seed(db, link="https://news.example/bad-date-filter")
                await db.commit()
                stmt = apply_article_filters(select(NewsArticle), start_date="not-a-date")
                return (await db.execute(stmt)).scalars().all()

        assert len(_run(_scenario())) == 1


class TestGetPaginatedArticles:
    def test_returns_total_count_and_page_of_results(self, session_factory):
        async def _scenario():
            async with session_factory() as db:
                for i in range(3):
                    await _seed(db, link=f"https://news.example/paged{i}")
                await db.commit()
                return await get_paginated_articles(db, page=1, page_size=2)

        result = _run(_scenario())
        assert result["total_count"] == 3
        assert result["page"] == 1
        assert result["page_size"] == 2
        assert len(result["articles"]) == 2

    def test_second_page_returns_remaining_articles(self, session_factory):
        async def _scenario():
            async with session_factory() as db:
                for i in range(3):
                    await _seed(db, link=f"https://news.example/paged2-{i}")
                await db.commit()
                return await get_paginated_articles(db, page=2, page_size=2)

        result = _run(_scenario())
        assert len(result["articles"]) == 1

    def test_combines_pagination_with_filters(self, session_factory):
        async def _scenario():
            async with session_factory() as db:
                await _seed(db, link="https://news.example/filtered-red", tlp="TLP:RED")
                await _seed(db, link="https://news.example/filtered-clear", tlp="TLP:CLEAR")
                await db.commit()
                return await get_paginated_articles(db, tlp="TLP:RED")

        result = _run(_scenario())
        assert result["total_count"] == 1
        assert result["articles"][0].link == "https://news.example/filtered-red"
