from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.features.git_recon.models.git_recon_models import GitReconSearch


async def create_search(
    db: AsyncSession,
    *,
    mode: str,
    target: str,
    status: str,
    error: str | None,
    repos_scanned: int,
    repos_failed: int,
    persons_found: int,
    result: dict | None,
) -> GitReconSearch:
    """Persist a completed (or failed) git_recon scan"""
    search = GitReconSearch(
        mode=mode,
        target=target,
        status=status,
        error=error,
        repos_scanned=repos_scanned,
        repos_failed=repos_failed,
        persons_found=persons_found,
        result=result,
    )
    db.add(search)
    await db.flush()
    await db.refresh(search)
    return search


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
