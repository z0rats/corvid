import datetime
from dataclasses import dataclass
from types import SimpleNamespace

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload


@dataclass(frozen=True)
class ScanColumns:
    """Per-feature column names `mark_completed`/`mark_cancelled`/`mark_failed` touch.

    The three scan-style models (MailSearch, MaigretSearch, GitReconSearch) don't
    agree on naming: `GitReconSearch.error` vs the other two's `error_message`, and
    `GitReconSearch` has no `completed_at` column at all (pass `None` for it).
    """

    error_column: str
    completed_at_column: str | None


async def create_running(db: AsyncSession, model: type, **fields):
    """Create a new row of `model` in the 'running' state.

    Shared by email_search, username_search, and git_recon: each starts its scan
    as a detached asyncio task and needs a row to report progress against before
    the scan itself has produced any results.
    """
    instance = model(status="running", **fields)
    db.add(instance)
    await db.flush()
    await db.refresh(instance)
    return instance


async def _get_by_id(db: AsyncSession, model: type, search_id: int):
    result = await db.execute(select(model).where(model.id == search_id))
    return result.scalar_one_or_none()


def _touch_completed_at(instance, columns: ScanColumns) -> None:
    if columns.completed_at_column is not None:
        setattr(instance, columns.completed_at_column, datetime.datetime.now(datetime.UTC))


async def mark_completed(
    db: AsyncSession, model: type, search_id: int, *, columns: ScanColumns, **fields
):
    """Mark a row as completed, applying whatever status fields the caller passes
    (counts, etc.). Callers that persist child rows (e.g. found-provider results)
    do so themselves right after calling this - this function never touches
    domain-specific row shapes."""
    instance = await _get_by_id(db, model, search_id)
    if not instance:
        return None

    instance.status = "completed"
    for key, value in fields.items():
        setattr(instance, key, value)
    _touch_completed_at(instance, columns)

    await db.flush()
    return instance


async def mark_cancelled(
    db: AsyncSession, model: type, search_id: int, *, columns: ScanColumns, **fields
):
    """Mark a row as cancelled, applying whatever status fields the caller passes.
    Not used by git_recon, which has no cancellation path."""
    instance = await _get_by_id(db, model, search_id)
    if not instance:
        return None

    instance.status = "cancelled"
    for key, value in fields.items():
        setattr(instance, key, value)
    _touch_completed_at(instance, columns)

    await db.flush()
    return instance


async def mark_failed(
    db: AsyncSession, model: type, search_id: int, *, columns: ScanColumns, error_message: str
):
    """Mark a row as failed, truncating the error message to fit the error column."""
    instance = await _get_by_id(db, model, search_id)
    if not instance:
        return None

    instance.status = "failed"
    setattr(instance, columns.error_column, error_message[:1000])
    _touch_completed_at(instance, columns)

    await db.flush()
    return instance


def make_scan_history_crud(model: type, order_by, relation=None) -> SimpleNamespace:
    """Build the list/get/get_with_results/delete quartet shared by every
    scan-style feature's CRUD module - across username_search, email_search, and
    git_recon these only ever differed in the model class, the column history is
    sorted by, and (except git_recon, whose results are a JSON blob column per
    ADR-0002, not a child table) the relationship to eager-load. Each feature's
    CRUD module still owns its own writes (e.g. add_site_results) directly.

    Returns a namespace of async functions rather than a class: nothing here
    holds state across calls, so there's no instance to construct or thread through.
    """

    async def list_runs(db: AsyncSession, skip: int = 0, limit: int = 100) -> list:
        result = await db.execute(select(model).order_by(order_by.desc()).offset(skip).limit(limit))
        return list(result.scalars().all())

    async def get_run(db: AsyncSession, search_id: int):
        return await _get_by_id(db, model, search_id)

    async def get_run_with_results(db: AsyncSession, search_id: int):
        if relation is None:
            return await get_run(db, search_id)
        result = await db.execute(
            select(model).where(model.id == search_id).options(selectinload(relation))
        )
        return result.scalar_one_or_none()

    async def delete_run(db: AsyncSession, search_id: int):
        instance = await get_run(db, search_id)
        if not instance:
            return None
        await db.delete(instance)
        await db.flush()
        return instance

    return SimpleNamespace(
        list=list_runs, get=get_run, get_with_results=get_run_with_results, delete=delete_run
    )
