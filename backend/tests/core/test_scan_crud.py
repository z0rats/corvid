"""Characterizes `create_running`/`mark_completed`/`mark_cancelled`/`mark_failed`
(core/scans/crud.py) against real tables, covering the three call shapes they
replace: email_search/username_search's create_search_run/complete_search_run/
cancel_search_run/fail_search_run, and git_recon's create_running_search/
complete_search/fail_search (no cancel path, no completed_at column). Same
engine-fixture pattern as test_scan_reconciliation.py.
"""

import asyncio
import datetime
from pathlib import Path

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker

from app.core.config.settings import settings
from app.core.database import Base, create_database_engine
from app.core.scans.crud import (
    ScanColumns,
    create_running,
    make_scan_history_crud,
    mark_cancelled,
    mark_completed,
    mark_failed,
)
from app.features.email_search.models.email_search_models import MailSearch
from app.features.git_recon.models.git_recon_models import GitReconSearch
from app.features.username_search.models.username_search_models import (
    MaigretSearch,
    MaigretSiteResult,
)

MAIGRET_COLUMNS = ScanColumns(error_column="error_message", completed_at_column="completed_at")
GIT_RECON_COLUMNS = ScanColumns(error_column="error", completed_at_column=None)


def _run(coro):
    return asyncio.run(coro)


@pytest.fixture
def engine(tmp_path: Path, monkeypatch):
    db_path = tmp_path / "scan_crud.db"
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


class TestCreateRunning:
    def test_creates_row_in_running_state(self, engine):
        session_factory = _session_factory(engine, MaigretSearch.__table__)

        async def _scenario():
            async with session_factory() as db:
                search = await create_running(db, MaigretSearch, username="alice", source="maigret")
                await db.commit()
                return search.id, search.status

        search_id, status = _run(_scenario())
        assert status == "running"
        assert search_id is not None


class TestMaigretSearchLikeModels:
    """MaigretSearch/MailSearch share the same shape: error_message + completed_at,
    and support cancel in addition to complete/fail."""

    def test_mark_completed_sets_status_fields_and_completed_at(self, engine):
        session_factory = _session_factory(engine, MaigretSearch.__table__)

        async def _scenario():
            async with session_factory() as db:
                running = MaigretSearch(username="alice", status="running")
                db.add(running)
                await db.commit()
                running_id = running.id

            async with session_factory() as db:
                search = await mark_completed(
                    db,
                    MaigretSearch,
                    running_id,
                    columns=MAIGRET_COLUMNS,
                    total_sites_checked=42,
                    found_count=3,
                )
                await db.commit()
                assert search is not None

            async with session_factory() as db:
                row = (
                    await db.execute(select(MaigretSearch).where(MaigretSearch.id == running_id))
                ).scalar_one()
                return row

        row = _run(_scenario())
        assert row.status == "completed"
        assert row.total_sites_checked == 42
        assert row.found_count == 3
        assert row.completed_at is not None

    def test_mark_cancelled_sets_status_and_completed_at(self, engine):
        session_factory = _session_factory(engine, MailSearch.__table__)

        async def _scenario():
            async with session_factory() as db:
                running = MailSearch(username="bob", status="running")
                db.add(running)
                await db.commit()
                running_id = running.id

            async with session_factory() as db:
                await mark_cancelled(
                    db,
                    MailSearch,
                    running_id,
                    columns=MAIGRET_COLUMNS,
                    total_providers_checked=5,
                    found_count=1,
                )
                await db.commit()

            async with session_factory() as db:
                row = (
                    await db.execute(select(MailSearch).where(MailSearch.id == running_id))
                ).scalar_one()
                return row

        row = _run(_scenario())
        assert row.status == "cancelled"
        assert row.total_providers_checked == 5
        assert row.completed_at is not None

    def test_mark_failed_sets_error_message_and_completed_at(self, engine):
        session_factory = _session_factory(engine, MailSearch.__table__)

        async def _scenario():
            async with session_factory() as db:
                running = MailSearch(username="carol", status="running")
                db.add(running)
                await db.commit()
                running_id = running.id

            async with session_factory() as db:
                await mark_failed(
                    db,
                    MailSearch,
                    running_id,
                    columns=MAIGRET_COLUMNS,
                    error_message="boom",
                )
                await db.commit()

            async with session_factory() as db:
                row = (
                    await db.execute(select(MailSearch).where(MailSearch.id == running_id))
                ).scalar_one()
                return row

        row = _run(_scenario())
        assert row.status == "failed"
        assert row.error_message == "boom"
        assert row.completed_at is not None

    def test_mark_completed_returns_none_for_missing_id(self, engine):
        session_factory = _session_factory(engine, MailSearch.__table__)

        async def _scenario():
            async with session_factory() as db:
                return await mark_completed(
                    db,
                    MailSearch,
                    999,
                    columns=MAIGRET_COLUMNS,
                    total_providers_checked=0,
                    found_count=0,
                )

        assert _run(_scenario()) is None


class TestGitReconSearchShape:
    """GitReconSearch has no completed_at column, names its error column `error`,
    and has no cancel path."""

    def test_mark_completed_does_not_touch_completed_at(self, engine):
        session_factory = _session_factory(engine, GitReconSearch.__table__)

        async def _scenario():
            async with session_factory() as db:
                running = GitReconSearch(mode="nickname", target="octocat", status="running")
                db.add(running)
                await db.commit()
                running_id = running.id

            async with session_factory() as db:
                await mark_completed(
                    db,
                    GitReconSearch,
                    running_id,
                    columns=GIT_RECON_COLUMNS,
                    repos_scanned=10,
                    repos_failed=1,
                    persons_found=2,
                    result={"ok": True},
                )
                await db.commit()

            async with session_factory() as db:
                row = (
                    await db.execute(select(GitReconSearch).where(GitReconSearch.id == running_id))
                ).scalar_one()
                return row

        row = _run(_scenario())
        assert row.status == "completed"
        assert row.repos_scanned == 10
        assert row.result == {"ok": True}

    def test_mark_failed_sets_error_without_completed_at(self, engine):
        session_factory = _session_factory(engine, GitReconSearch.__table__)

        async def _scenario():
            async with session_factory() as db:
                running = GitReconSearch(mode="nickname", target="octocat", status="running")
                db.add(running)
                await db.commit()
                running_id = running.id

            async with session_factory() as db:
                await mark_failed(
                    db,
                    GitReconSearch,
                    running_id,
                    columns=GIT_RECON_COLUMNS,
                    error_message="scan failed",
                )
                await db.commit()

            async with session_factory() as db:
                row = (
                    await db.execute(select(GitReconSearch).where(GitReconSearch.id == running_id))
                ).scalar_one()
                return row

        row = _run(_scenario())
        assert row.status == "failed"
        assert row.error == "scan failed"


class TestMakeScanHistoryCrud:
    """`make_scan_history_crud` replaces the near-identical list/get/
    get_with_results/delete quartet that username_search_crud.py,
    email_search_crud.py, and git_recon_crud.py used to each hand-write. One
    build with a child relation (MaigretSearch/MaigretSiteResult) and one
    without (GitReconSearch, whose results are a JSON blob column) cover both
    shapes those three modules actually need."""

    def test_list_orders_most_recent_first_and_paginates(self, engine):
        session_factory = _session_factory(engine, MaigretSearch.__table__)
        history = make_scan_history_crud(MaigretSearch, MaigretSearch.started_at)

        async def _scenario():
            async with session_factory() as db:
                for i in range(3):
                    row = MaigretSearch(username=f"user{i}", status="completed")
                    row.started_at = datetime.datetime(2024, 1, i + 1, tzinfo=datetime.UTC)
                    db.add(row)
                await db.commit()

            async with session_factory() as db:
                return await history.list(db, skip=1, limit=1)

        rows = _run(_scenario())
        assert [row.username for row in rows] == ["user1"]

    def test_get_returns_none_for_missing_id(self, engine):
        session_factory = _session_factory(engine, GitReconSearch.__table__)
        history = make_scan_history_crud(GitReconSearch, GitReconSearch.searched_at)

        async def _scenario():
            async with session_factory() as db:
                return await history.get(db, 999)

        assert _run(_scenario()) is None

    def test_get_with_results_eager_loads_the_given_relation(self, engine):
        session_factory = _session_factory(
            engine, MaigretSearch.__table__, MaigretSiteResult.__table__
        )
        history = make_scan_history_crud(
            MaigretSearch, MaigretSearch.started_at, relation=MaigretSearch.site_results
        )

        async def _scenario():
            async with session_factory() as db:
                search = MaigretSearch(username="alice", status="completed")
                db.add(search)
                await db.flush()
                db.add(MaigretSiteResult(search_id=search.id, site_name="GitHub", url_user="alice"))
                await db.commit()
                search_id = search.id

            async with session_factory() as db:
                return await history.get_with_results(db, search_id)

        row = _run(_scenario())
        assert len(row.site_results) == 1
        assert row.site_results[0].site_name == "GitHub"

    def test_get_with_results_falls_back_to_plain_get_without_a_relation(self, engine):
        session_factory = _session_factory(engine, GitReconSearch.__table__)
        history = make_scan_history_crud(GitReconSearch, GitReconSearch.searched_at)

        async def _scenario():
            async with session_factory() as db:
                search = GitReconSearch(mode="nickname", target="octocat", status="completed")
                db.add(search)
                await db.commit()
                search_id = search.id

            async with session_factory() as db:
                return await history.get_with_results(db, search_id)

        row = _run(_scenario())
        assert row is not None
        assert row.target == "octocat"

    def test_delete_removes_the_row_and_returns_none_for_missing_id(self, engine):
        session_factory = _session_factory(engine, GitReconSearch.__table__)
        history = make_scan_history_crud(GitReconSearch, GitReconSearch.searched_at)

        async def _scenario():
            async with session_factory() as db:
                search = GitReconSearch(mode="nickname", target="octocat", status="completed")
                db.add(search)
                await db.commit()
                search_id = search.id

            async with session_factory() as db:
                deleted = await history.delete(db, search_id)
                await db.commit()

            async with session_factory() as db:
                still_there = await history.get(db, search_id)
                missing = await history.delete(db, 999)
                return deleted, still_there, missing

        deleted, still_there, missing = _run(_scenario())
        assert deleted is not None
        assert still_there is None
        assert missing is None
