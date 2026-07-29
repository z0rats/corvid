from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.scans.crud import ScanColumns, create_running, mark_cancelled, mark_completed, mark_failed
from app.core.scans.reconciliation import mark_stale_running_as_failed
from app.features.username_search.models.username_search_models import MaigretSearch, MaigretSiteResult

_COLUMNS = ScanColumns(error_column="error_message", completed_at_column="completed_at")


async def create_search_run(
    db: AsyncSession, username: str, tags: list[str] | None = None, source: str = "maigret"
) -> MaigretSearch:
    """Create a new search run in the 'running' state"""
    return await create_running(db, MaigretSearch, username=username, tags=tags, source=source)


async def complete_search_run(
    db: AsyncSession,
    search_id: int,
    total_sites_checked: int,
    found_sites: list[dict],
) -> MaigretSearch | None:
    """Mark a search run as completed, storing its found-site results"""
    search = await mark_completed(
        db, MaigretSearch, search_id,
        columns=_COLUMNS,
        total_sites_checked=total_sites_checked,
        found_count=len(found_sites),
    )
    if not search:
        return None

    for site in found_sites:
        db.add(MaigretSiteResult(
            search_id=search_id,
            site_name=site["site_name"],
            url_user=site["url_user"],
            http_status=site.get("http_status"),
            extra=site.get("extra"),
        ))

    await db.flush()
    return search


async def cancel_search_run(
    db: AsyncSession,
    search_id: int,
    total_sites_checked: int,
    found_sites: list[dict],
) -> MaigretSearch | None:
    """Mark a search run as cancelled, storing whatever found-site results
    were captured before cancellation."""
    search = await mark_cancelled(
        db, MaigretSearch, search_id,
        columns=_COLUMNS,
        total_sites_checked=total_sites_checked,
        found_count=len(found_sites),
    )
    if not search:
        return None

    for site in found_sites:
        db.add(MaigretSiteResult(
            search_id=search_id,
            site_name=site["site_name"],
            url_user=site["url_user"],
            http_status=site.get("http_status"),
            extra=site.get("extra"),
        ))

    await db.flush()
    return search


async def fail_search_run(db: AsyncSession, search_id: int, error_message: str) -> MaigretSearch | None:
    """Mark a search run as failed"""
    return await mark_failed(db, MaigretSearch, search_id, columns=_COLUMNS, error_message=error_message)


async def interrupt_running_search_runs(db: AsyncSession) -> int:
    """Mark any run still 'running' as failed - see `mark_stale_running_as_failed`'s
    docstring for why this is needed (an in-memory asyncio task doesn't survive
    a process restart)."""
    return await mark_stale_running_as_failed(
        db, MaigretSearch,
        error_column=_COLUMNS.error_column,
        error_message="Interrupted by server restart",
        completed_at_column=_COLUMNS.completed_at_column,
    )


async def list_search_runs(db: AsyncSession, skip: int = 0, limit: int = 100) -> list[MaigretSearch]:
    """List past search runs, most recent first"""
    result = await db.execute(
        select(MaigretSearch).order_by(MaigretSearch.started_at.desc()).offset(skip).limit(limit)
    )
    return list(result.scalars().all())


async def get_search_run(db: AsyncSession, search_id: int) -> MaigretSearch | None:
    """Get a search run by ID, without its site results"""
    result = await db.execute(select(MaigretSearch).where(MaigretSearch.id == search_id))
    return result.scalar_one_or_none()


async def get_search_run_with_results(db: AsyncSession, search_id: int) -> MaigretSearch | None:
    """Get a search run by ID, including its found-site results"""
    result = await db.execute(
        select(MaigretSearch)
        .where(MaigretSearch.id == search_id)
        .options(selectinload(MaigretSearch.site_results))
    )
    return result.scalar_one_or_none()


async def delete_search_run(db: AsyncSession, search_id: int) -> MaigretSearch | None:
    """Delete a search run and its site results"""
    search = await get_search_run(db, search_id)
    if not search:
        return None

    await db.delete(search)
    await db.flush()
    return search
