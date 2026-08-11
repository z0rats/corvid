from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.scans.crud import ScanColumns
from app.core.scans.reconciliation import mark_stale_running_as_failed
from app.features.email_search.models.email_search_models import MailSearch, MailSearchResult

# ScanRun.execute() now owns row create/complete/cancel/fail directly via
# core/scans/crud.py, using this.
SCAN_COLUMNS = ScanColumns(error_column="error_message", completed_at_column="completed_at")


async def add_provider_results(db: AsyncSession, search_id: int, found_providers: list[dict]) -> None:
    """Persist found-provider child rows for a search run. Called by run_work
    once it has results (on both normal completion and mid-scan cancellation) -
    ScanRun's generic mark_completed/mark_cancelled only ever touch scalar
    columns on the parent row, never these child rows."""
    for provider in found_providers:
        db.add(MailSearchResult(
            search_id=search_id,
            provider_name=provider["provider_name"],
            emails=provider["emails"],
            extra=provider.get("extra"),
        ))
    await db.flush()


async def interrupt_running_search_runs(db: AsyncSession) -> int:
    """Mark any run still 'running' as failed - see `mark_stale_running_as_failed`'s
    docstring for why this is needed (an in-memory asyncio task doesn't survive
    a process restart)."""
    return await mark_stale_running_as_failed(
        db, MailSearch,
        error_column=SCAN_COLUMNS.error_column,
        error_message="Interrupted by server restart",
        completed_at_column=SCAN_COLUMNS.completed_at_column,
    )


async def list_search_runs(db: AsyncSession, skip: int = 0, limit: int = 100) -> list[MailSearch]:
    """List past search runs, most recent first"""
    result = await db.execute(
        select(MailSearch).order_by(MailSearch.started_at.desc()).offset(skip).limit(limit)
    )
    return list(result.scalars().all())


async def get_search_run(db: AsyncSession, search_id: int) -> MailSearch | None:
    """Get a search run by ID, without its provider results"""
    result = await db.execute(select(MailSearch).where(MailSearch.id == search_id))
    return result.scalar_one_or_none()


async def get_search_run_with_results(db: AsyncSession, search_id: int) -> MailSearch | None:
    """Get a search run by ID, including its found-provider results"""
    result = await db.execute(
        select(MailSearch)
        .where(MailSearch.id == search_id)
        .options(selectinload(MailSearch.provider_results))
    )
    return result.scalar_one_or_none()


async def delete_search_run(db: AsyncSession, search_id: int) -> MailSearch | None:
    """Delete a search run and its provider results"""
    search = await get_search_run(db, search_id)
    if not search:
        return None

    await db.delete(search)
    await db.flush()
    return search
