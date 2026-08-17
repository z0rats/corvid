import datetime

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.scans.crud import ScanColumns
from app.core.scans.reconciliation import mark_stale_running_as_failed
from app.features.ru_business_check.models.ru_business_check_models import RuBusinessCheckSearch

SCAN_COLUMNS = ScanColumns(error_column="error", completed_at_column="completed_at")


async def interrupt_running_searches(db: AsyncSession) -> int:
    """Mark any search still 'running' as failed - see `mark_stale_running_as_failed`'s
    docstring for why this is needed (an in-memory asyncio task doesn't survive a
    process restart)."""
    return await mark_stale_running_as_failed(
        db,
        RuBusinessCheckSearch,
        error_column=SCAN_COLUMNS.error_column,
        error_message="Interrupted by server restart",
        completed_at_column=SCAN_COLUMNS.completed_at_column,
    )


async def get_search(db: AsyncSession, search_id: int) -> RuBusinessCheckSearch | None:
    result = await db.execute(
        select(RuBusinessCheckSearch).where(RuBusinessCheckSearch.id == search_id)
    )
    return result.scalar_one_or_none()


async def list_searches(
    db: AsyncSession, skip: int = 0, limit: int = 100
) -> list[RuBusinessCheckSearch]:
    result = await db.execute(
        select(RuBusinessCheckSearch)
        .order_by(RuBusinessCheckSearch.searched_at.desc())
        .offset(skip)
        .limit(limit)
    )
    return list(result.scalars().all())


async def find_recent_completed_search_by_query(
    db: AsyncSession, query: str, *, max_age: datetime.timedelta
) -> RuBusinessCheckSearch | None:
    """Most recent completed scan for the exact same (normalized) raw query within
    `max_age` - backs the TTL cache (decision: a repeated lookup serves the cached row
    rather than re-hitting egrul.nalog.ru/service.nalog.ru, unless explicitly
    force-refreshed). Matches on the raw `query` string rather than a resolved ИНН,
    since resolving it requires the very ЕГРЮЛ call the cache exists to avoid - querying
    once by name and again by ИНН for the same entity is a known miss, acceptable for
    Stage 1's simplicity."""
    cutoff = datetime.datetime.now(datetime.UTC) - max_age
    result = await db.execute(
        select(RuBusinessCheckSearch)
        .where(
            RuBusinessCheckSearch.query == query,
            RuBusinessCheckSearch.status == "completed",
            RuBusinessCheckSearch.searched_at >= cutoff,
        )
        .order_by(RuBusinessCheckSearch.searched_at.desc())
        .limit(1)
    )
    return result.scalar_one_or_none()


async def delete_search(db: AsyncSession, search_id: int) -> RuBusinessCheckSearch | None:
    search = await get_search(db, search_id)
    if not search:
        return None
    await db.delete(search)
    await db.flush()
    return search


async def delete_expired_searches(db: AsyncSession, retention_days: int) -> int:
    """Delete searches (including their raw scraped payloads) older than `retention_days`.
    `retention_days == 0` disables the sweep (unlimited retention) - same convention as
    newsfeed's article retention."""
    if retention_days == 0:
        return 0
    cutoff = datetime.datetime.now(datetime.UTC) - datetime.timedelta(days=retention_days)
    result = await db.execute(
        delete(RuBusinessCheckSearch).where(RuBusinessCheckSearch.searched_at < cutoff)
    )
    await db.flush()
    return result.rowcount
