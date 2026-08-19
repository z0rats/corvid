import asyncio
import datetime

import pytest

from app.features.email_search.crud.email_search_crud import (
    add_provider_results,
    delete_search_run,
    get_search_run,
    get_search_run_with_results,
    interrupt_running_search_runs,
    list_search_runs,
)
from app.features.email_search.models.email_search_models import MailSearch, MailSearchResult


def _run(coro):
    return asyncio.run(coro)


@pytest.fixture
def session_factory(make_session_factory):
    return make_session_factory([MailSearch.__table__, MailSearchResult.__table__])


def _create_search(username="alice", status="running"):
    return MailSearch(username=username, status=status)


class TestAddProviderResults:
    def test_persists_one_row_per_found_provider(self, session_factory):
        async def _scenario():
            async with session_factory() as db:
                search = _create_search()
                db.add(search)
                await db.flush()
                search_id = search.id
                await add_provider_results(
                    db,
                    search_id,
                    [
                        {"provider_name": "gmail", "emails": ["a@gmail.com"]},
                        {"provider_name": "yandex", "emails": ["a@yandex.com"], "extra": {"x": 1}},
                    ],
                )
                await db.commit()

            async with session_factory() as db:
                return await get_search_run_with_results(db, search_id)

        run = _run(_scenario())
        assert len(run.provider_results) == 2
        by_name = {r.provider_name: r for r in run.provider_results}
        assert by_name["gmail"].emails == ["a@gmail.com"]
        assert by_name["yandex"].extra == {"x": 1}

    def test_is_a_no_op_for_an_empty_list(self, session_factory):
        async def _scenario():
            async with session_factory() as db:
                search = _create_search()
                db.add(search)
                await db.flush()
                search_id = search.id
                await add_provider_results(db, search_id, [])
                await db.commit()

            async with session_factory() as db:
                return await get_search_run_with_results(db, search_id)

        run = _run(_scenario())
        assert run.provider_results == []


class TestInterruptRunningSearchRuns:
    def test_marks_running_rows_as_failed_and_returns_the_count(self, session_factory):
        async def _scenario():
            async with session_factory() as db:
                db.add(_create_search(status="running"))
                db.add(_create_search(status="running"))
                db.add(_create_search(status="completed"))
                await db.commit()

            async with session_factory() as db:
                count = await interrupt_running_search_runs(db)
                await db.commit()

            async with session_factory() as db:
                runs = await list_search_runs(db)
                return count, {r.status for r in runs}

        count, statuses = _run(_scenario())
        assert count == 2
        assert statuses == {"failed", "completed"}


class TestListSearchRuns:
    def test_orders_most_recent_first(self, session_factory):
        async def _scenario():
            async with session_factory() as db:
                older = _create_search(username="older")
                older.started_at = datetime.datetime(2020, 1, 1, tzinfo=datetime.UTC)
                newer = _create_search(username="newer")
                newer.started_at = datetime.datetime(2024, 1, 1, tzinfo=datetime.UTC)
                db.add(older)
                db.add(newer)
                await db.commit()

            async with session_factory() as db:
                return await list_search_runs(db)

        runs = _run(_scenario())
        assert [r.username for r in runs] == ["newer", "older"]

    def test_respects_skip_and_limit(self, session_factory):
        async def _scenario():
            async with session_factory() as db:
                for i in range(5):
                    search = _create_search(username=f"user{i}")
                    search.started_at = datetime.datetime(2024, 1, i + 1, tzinfo=datetime.UTC)
                    db.add(search)
                await db.commit()

            async with session_factory() as db:
                return await list_search_runs(db, skip=1, limit=2)

        runs = _run(_scenario())
        assert [r.username for r in runs] == ["user3", "user2"]


class TestGetSearchRun:
    def test_returns_none_for_an_unknown_id(self, session_factory):
        async def _scenario():
            async with session_factory() as db:
                return await get_search_run(db, 999)

        assert _run(_scenario()) is None

    def test_does_not_eagerly_load_provider_results(self, session_factory):
        async def _scenario():
            async with session_factory() as db:
                search = _create_search()
                db.add(search)
                await db.flush()
                search_id = search.id
                await add_provider_results(
                    db, search_id, [{"provider_name": "gmail", "emails": ["a@gmail.com"]}]
                )
                await db.commit()

            async with session_factory() as db:
                return await get_search_run(db, search_id)

        run = _run(_scenario())
        assert run is not None


class TestGetSearchRunWithResults:
    def test_returns_none_for_an_unknown_id(self, session_factory):
        async def _scenario():
            async with session_factory() as db:
                return await get_search_run_with_results(db, 999)

        assert _run(_scenario()) is None


class TestDeleteSearchRun:
    def test_returns_none_for_an_unknown_id(self, session_factory):
        async def _scenario():
            async with session_factory() as db:
                return await delete_search_run(db, 999)

        assert _run(_scenario()) is None

    def test_deletes_the_search_and_its_provider_results(self, session_factory):
        async def _scenario():
            async with session_factory() as db:
                search = _create_search()
                db.add(search)
                await db.flush()
                search_id = search.id
                await add_provider_results(
                    db, search_id, [{"provider_name": "gmail", "emails": ["a@gmail.com"]}]
                )
                await db.commit()

            async with session_factory() as db:
                deleted = await delete_search_run(db, search_id)
                await db.commit()

            async with session_factory() as db:
                still_there = await get_search_run(db, search_id)
                return deleted, still_there

        deleted, still_there = _run(_scenario())
        assert deleted is not None
        assert still_there is None
