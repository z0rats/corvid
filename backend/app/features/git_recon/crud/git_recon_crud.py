from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.features.git_recon.models.git_recon_models import GitReconSearch


async def create_running_search(db: AsyncSession, *, mode: str, target: str) -> GitReconSearch:
    """Create a new git_recon search in the 'running' state, before the scan itself starts"""
    search = GitReconSearch(mode=mode, target=target, status="running")
    db.add(search)
    await db.flush()
    await db.refresh(search)
    return search


async def complete_search(
    db: AsyncSession,
    search_id: int,
    *,
    repos_scanned: int,
    repos_failed: int,
    persons_found: int,
    result: dict,
) -> GitReconSearch | None:
    """Mark a search as completed, storing its result"""
    search = await get_search(db, search_id)
    if not search:
        return None

    search.status = "completed"
    search.repos_scanned = repos_scanned
    search.repos_failed = repos_failed
    search.persons_found = persons_found
    search.result = result
    await db.flush()
    return search


async def fail_search(db: AsyncSession, search_id: int, *, error: str) -> GitReconSearch | None:
    """Mark a search as failed"""
    search = await get_search(db, search_id)
    if not search:
        return None

    search.status = "failed"
    search.error = error[:1000]
    await db.flush()
    return search


async def interrupt_running_searches(db: AsyncSession) -> int:
    """Mark any search still 'running' as failed.

    The scan task driving it is an in-memory asyncio task (see run_scan_task()/
    the SSE route handler), so it doesn't survive a process restart - without
    this, a scan interrupted by a container stop/crash would stay 'running'
    forever with no way for the frontend to tell it apart from one still in
    progress.
    """
    result = await db.execute(
        update(GitReconSearch)
        .where(GitReconSearch.status == "running")
        .values(status="failed", error="Interrupted by server restart")
    )
    await db.flush()
    return result.rowcount


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
