from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.scans.crud import ScanColumns
from app.core.scans.reconciliation import mark_stale_running_as_failed
from app.features.git_recon.models.git_recon_models import GitReconSearch

# ScanRun.execute() now owns row create/complete/cancel/fail directly via
# core/scans/crud.py, using this. GitReconSearch has no completed_at column and
# names its error column `error` (not `error_message`, unlike the other two
# scan-style models).
SCAN_COLUMNS = ScanColumns(error_column="error", completed_at_column=None)


async def interrupt_running_searches(db: AsyncSession) -> int:
    """Mark any search still 'running' as failed - see `mark_stale_running_as_failed`'s
    docstring for why this is needed (an in-memory asyncio task doesn't survive
    a process restart)."""
    return await mark_stale_running_as_failed(
        db,
        GitReconSearch,
        error_column=SCAN_COLUMNS.error_column,
        error_message="Interrupted by server restart",
        completed_at_column=SCAN_COLUMNS.completed_at_column,
    )


async def get_search(db: AsyncSession, search_id: int) -> GitReconSearch | None:
    """Get a search by ID, including its persisted result"""
    result = await db.execute(select(GitReconSearch).where(GitReconSearch.id == search_id))
    return result.scalar_one_or_none()


async def list_searches(db: AsyncSession, skip: int = 0, limit: int = 100) -> list[GitReconSearch]:
    """List past searches, most recent first"""
    result = await db.execute(
        select(GitReconSearch).order_by(GitReconSearch.searched_at.desc()).offset(skip).limit(limit)
    )
    return list(result.scalars().all())


async def delete_search(db: AsyncSession, search_id: int) -> GitReconSearch | None:
    """Delete a search"""
    search = await get_search(db, search_id)
    if not search:
        return None

    await db.delete(search)
    await db.flush()
    return search
