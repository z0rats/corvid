"""Characterizes `mark_stale_running_as_failed` (core/scans/reconciliation.py)
against real tables, covering the three call shapes it replaces:
`username_search`/`email_search`'s `interrupt_running_search_runs` (sets
`completed_at`, error column named `error_message`) and `git_recon`'s
`interrupt_running_searches` (no `completed_at` column, error column named
`error`). Same engine-fixture pattern as test_fk_cascade_delete.py.
"""
import asyncio
from pathlib import Path

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker

from app.core.config.settings import settings
from app.core.database import Base, create_database_engine
from app.core.scans.reconciliation import mark_stale_running_as_failed
from app.features.email_search.models.email_search_models import MailSearch
from app.features.git_recon.models.git_recon_models import GitReconSearch
from app.features.username_search.models.username_search_models import MaigretSearch


def _run(coro):
    return asyncio.run(coro)


@pytest.fixture
def engine(tmp_path: Path, monkeypatch):
    db_path = tmp_path / "reconciliation.db"
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


class TestMaigretSearchLikeModels:
    """MaigretSearch/MailSearch share the same shape: error_message + completed_at."""

    def test_running_rows_marked_failed_with_message_and_completed_at(self, engine):
        session_factory = _session_factory(engine, MaigretSearch.__table__)

        async def _scenario():
            async with session_factory() as db:
                running = MaigretSearch(username="alice", status="running")
                db.add(running)
                await db.commit()
                running_id = running.id

            async with session_factory() as db:
                count = await mark_stale_running_as_failed(
                    db, MaigretSearch,
                    error_column="error_message",
                    error_message="Interrupted by server restart",
                    completed_at_column="completed_at",
                )
                await db.commit()

            async with session_factory() as db:
                row = (await db.execute(
                    select(MaigretSearch).where(MaigretSearch.id == running_id)
                )).scalar_one()
                return count, row

        count, row = _run(_scenario())
        assert count == 1
        assert row.status == "failed"
        assert row.error_message == "Interrupted by server restart"
        assert row.completed_at is not None

    def test_non_running_rows_are_untouched(self, engine):
        session_factory = _session_factory(engine, MaigretSearch.__table__)

        async def _scenario():
            async with session_factory() as db:
                completed = MaigretSearch(username="bob", status="completed")
                db.add(completed)
                await db.commit()
                completed_id = completed.id

            async with session_factory() as db:
                count = await mark_stale_running_as_failed(
                    db, MaigretSearch,
                    error_column="error_message",
                    error_message="Interrupted by server restart",
                    completed_at_column="completed_at",
                )
                await db.commit()

            async with session_factory() as db:
                row = (await db.execute(
                    select(MaigretSearch).where(MaigretSearch.id == completed_id)
                )).scalar_one()
                return count, row

        count, row = _run(_scenario())
        assert count == 0
        assert row.status == "completed"
        assert row.completed_at is None

    def test_multiple_running_rows_all_marked(self, engine):
        session_factory = _session_factory(engine, MailSearch.__table__)

        async def _scenario():
            async with session_factory() as db:
                db.add_all([
                    MailSearch(username="a", status="running"),
                    MailSearch(username="b", status="running"),
                    MailSearch(username="c", status="failed"),
                ])
                await db.commit()

            async with session_factory() as db:
                count = await mark_stale_running_as_failed(
                    db, MailSearch,
                    error_column="error_message",
                    error_message="Interrupted by server restart",
                    completed_at_column="completed_at",
                )
                await db.commit()
                return count

        assert _run(_scenario()) == 2


class TestGitReconSearchShape:
    """GitReconSearch has no completed_at column and names its error column `error`."""

    def test_running_rows_marked_failed_without_completed_at(self, engine):
        session_factory = _session_factory(engine, GitReconSearch.__table__)

        async def _scenario():
            async with session_factory() as db:
                running = GitReconSearch(mode="nickname", target="octocat", status="running")
                db.add(running)
                await db.commit()
                running_id = running.id

            async with session_factory() as db:
                count = await mark_stale_running_as_failed(
                    db, GitReconSearch,
                    error_column="error",
                    error_message="Interrupted by server restart",
                    completed_at_column=None,
                )
                await db.commit()

            async with session_factory() as db:
                row = (await db.execute(
                    select(GitReconSearch).where(GitReconSearch.id == running_id)
                )).scalar_one()
                return count, row

        count, row = _run(_scenario())
        assert count == 1
        assert row.status == "failed"
        assert row.error == "Interrupted by server restart"
