import datetime
from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession


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
        setattr(instance, columns.completed_at_column, datetime.datetime.now(datetime.timezone.utc))


async def mark_completed(db: AsyncSession, model: type, search_id: int, *, columns: ScanColumns, **fields):
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


async def mark_cancelled(db: AsyncSession, model: type, search_id: int, *, columns: ScanColumns, **fields):
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


async def mark_failed(db: AsyncSession, model: type, search_id: int, *, columns: ScanColumns, error_message: str):
    """Mark a row as failed, truncating the error message to fit the error column."""
    instance = await _get_by_id(db, model, search_id)
    if not instance:
        return None

    instance.status = "failed"
    setattr(instance, columns.error_column, error_message[:1000])
    _touch_completed_at(instance, columns)

    await db.flush()
    return instance
