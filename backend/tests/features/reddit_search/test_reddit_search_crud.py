import asyncio

import pytest

from app.features.reddit_search.crud.reddit_search_crud import (
    add_results,
    create_search,
    delete_search,
    get_search,
    get_search_with_results,
    list_searches,
)
from app.features.reddit_search.models.reddit_search_models import RedditSearch, RedditSearchResult


def _run(coro):
    return asyncio.run(coro)


@pytest.fixture
def session_factory(make_session_factory):
    return make_session_factory([RedditSearch.__table__, RedditSearchResult.__table__])


def _row(reddit_id, created_utc=100, kind="post", **overrides):
    defaults = dict(
        kind=kind,
        reddit_id=reddit_id,
        subreddit="python",
        title="t",
        body="b",
        score=1,
        num_comments=0,
        permalink="/r/python/x",
        created_utc=created_utc,
        over_18=False,
        removed=False,
        deleted=False,
        extra=None,
    )
    return {**defaults, **overrides}


class TestCreateSearch:
    def test_persists_the_given_filters(self, session_factory):
        async def _scenario():
            async with session_factory() as db:
                return await create_search(
                    db,
                    "spez",
                    subreddit_filter="python",
                    date_from=100,
                    date_to=200,
                    include_nsfw=False,
                )

        search = _run(_scenario())
        assert search.id is not None
        assert search.username == "spez"
        assert search.subreddit_filter == "python"
        assert search.include_nsfw is False


class TestGetSearch:
    def test_returns_none_for_an_unknown_id(self, session_factory):
        async def _scenario():
            async with session_factory() as db:
                return await get_search(db, 999)

        assert _run(_scenario()) is None


class TestGetSearchWithResults:
    def test_includes_persisted_results(self, session_factory):
        async def _scenario():
            async with session_factory() as db:
                search = await create_search(
                    db,
                    "spez",
                    subreddit_filter=None,
                    date_from=None,
                    date_to=None,
                    include_nsfw=True,
                )
                await db.commit()
                search_id = search.id
                await add_results(db, search_id, "post", [_row("a1")])
                await db.commit()

            async with session_factory() as db:
                return await get_search_with_results(db, search_id)

        search = _run(_scenario())
        assert len(search.results) == 1
        assert search.results[0].reddit_id == "a1"

    def test_returns_none_for_an_unknown_id(self, session_factory):
        async def _scenario():
            async with session_factory() as db:
                return await get_search_with_results(db, 999)

        assert _run(_scenario()) is None


class TestListSearches:
    def test_pairs_each_search_with_its_result_count(self, session_factory):
        async def _scenario():
            async with session_factory() as db:
                search = await create_search(
                    db,
                    "spez",
                    subreddit_filter=None,
                    date_from=None,
                    date_to=None,
                    include_nsfw=True,
                )
                await db.commit()
                search_id = search.id
                await add_results(db, search_id, "post", [_row("a1"), _row("a2")])
                await db.commit()

            async with session_factory() as db:
                return await list_searches(db)

        rows = _run(_scenario())
        assert len(rows) == 1
        search, count = rows[0]
        assert search.username == "spez"
        assert count == 2

    def test_a_search_with_no_results_yet_counts_as_zero(self, session_factory):
        async def _scenario():
            async with session_factory() as db:
                await create_search(
                    db,
                    "spez",
                    subreddit_filter=None,
                    date_from=None,
                    date_to=None,
                    include_nsfw=True,
                )
                await db.commit()

            async with session_factory() as db:
                return await list_searches(db)

        rows = _run(_scenario())
        assert rows[0][1] == 0

    def test_orders_most_recently_searched_first(self, session_factory):
        import datetime

        async def _scenario():
            async with session_factory() as db:
                older = await create_search(
                    db,
                    "older",
                    subreddit_filter=None,
                    date_from=None,
                    date_to=None,
                    include_nsfw=True,
                )
                older.searched_at = datetime.datetime(2020, 1, 1, tzinfo=datetime.UTC)
                newer = await create_search(
                    db,
                    "newer",
                    subreddit_filter=None,
                    date_from=None,
                    date_to=None,
                    include_nsfw=True,
                )
                newer.searched_at = datetime.datetime(2024, 1, 1, tzinfo=datetime.UTC)
                await db.commit()

            async with session_factory() as db:
                return await list_searches(db)

        rows = _run(_scenario())
        assert [r[0].username for r in rows] == ["newer", "older"]


class TestAddResults:
    def test_persists_new_rows(self, session_factory):
        async def _scenario():
            async with session_factory() as db:
                search = await create_search(
                    db,
                    "spez",
                    subreddit_filter=None,
                    date_from=None,
                    date_to=None,
                    include_nsfw=True,
                )
                await db.commit()
                search_id = search.id
                added = await add_results(db, search_id, "post", [_row("a1"), _row("a2")])
                await db.commit()
                return search_id, [r.reddit_id for r in added]

        search_id, added_ids = _run(_scenario())
        assert added_ids == ["a1", "a2"]

    def test_is_idempotent_for_a_kind_reddit_id_pair_already_stored(self, session_factory):
        async def _scenario():
            async with session_factory() as db:
                search = await create_search(
                    db,
                    "spez",
                    subreddit_filter=None,
                    date_from=None,
                    date_to=None,
                    include_nsfw=True,
                )
                await db.commit()
                search_id = search.id
                await add_results(db, search_id, "post", [_row("a1")])
                await db.commit()

            async with session_factory() as db:
                # Re-fetching the same page (e.g. paging back) must not duplicate a1.
                second = await add_results(db, search_id, "post", [_row("a1"), _row("a2")])
                await db.commit()
                return second

        second_batch = _run(_scenario())
        assert [r.reddit_id for r in second_batch] == ["a2"]

    def test_the_same_reddit_id_can_exist_as_both_a_post_and_a_comment(self, session_factory):
        async def _scenario():
            async with session_factory() as db:
                search = await create_search(
                    db,
                    "spez",
                    subreddit_filter=None,
                    date_from=None,
                    date_to=None,
                    include_nsfw=True,
                )
                await db.commit()
                search_id = search.id
                await add_results(db, search_id, "post", [_row("shared_id", kind="post")])
                await db.commit()
                added_as_comment = await add_results(
                    db, search_id, "comment", [_row("shared_id", kind="comment")]
                )
                await db.commit()
                return added_as_comment

        added = _run(_scenario())
        assert len(added) == 1

    def test_returns_an_empty_list_for_no_rows(self, session_factory):
        async def _scenario():
            async with session_factory() as db:
                search = await create_search(
                    db,
                    "spez",
                    subreddit_filter=None,
                    date_from=None,
                    date_to=None,
                    include_nsfw=True,
                )
                await db.commit()
                return await add_results(db, search.id, "post", [])

        assert _run(_scenario()) == []


class TestDeleteSearch:
    def test_returns_none_for_an_unknown_id(self, session_factory):
        async def _scenario():
            async with session_factory() as db:
                return await delete_search(db, 999)

        assert _run(_scenario()) is None

    def test_deletes_the_search_and_its_results(self, session_factory):
        async def _scenario():
            async with session_factory() as db:
                search = await create_search(
                    db,
                    "spez",
                    subreddit_filter=None,
                    date_from=None,
                    date_to=None,
                    include_nsfw=True,
                )
                await db.commit()
                search_id = search.id
                await add_results(db, search_id, "post", [_row("a1")])
                await db.commit()

            async with session_factory() as db:
                deleted = await delete_search(db, search_id)
                await db.commit()

            async with session_factory() as db:
                still_there = await get_search(db, search_id)
                return deleted, still_there

        deleted, still_there = _run(_scenario())
        assert deleted is not None
        assert still_there is None
