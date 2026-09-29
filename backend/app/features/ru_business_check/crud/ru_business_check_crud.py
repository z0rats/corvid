import datetime

from sqlalchemy import delete, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.scans.crud import ScanColumns
from app.core.scans.feature import ScanFeature
from app.features.ru_business_check.config.ru_business_check_config import FEATURE_NAME
from app.features.ru_business_check.models.ru_business_check_models import RuBusinessCheckSearch

RU_BUSINESS_CHECK_SCANS = ScanFeature(
    name=FEATURE_NAME,
    model=RuBusinessCheckSearch,
    columns=ScanColumns(error_column="error", completed_at_column="completed_at"),
    order_by=RuBusinessCheckSearch.searched_at,
)


async def find_recent_completed_search_by_query(
    db: AsyncSession, query: str, *, max_age: datetime.timedelta
) -> RuBusinessCheckSearch | None:
    """Most recent completed scan for the exact same (normalized) raw query within
    `max_age` - backs the TTL cache (decision: a repeated lookup serves the cached row
    rather than re-hitting egrul.nalog.ru/service.nalog.ru, unless explicitly
    force-refreshed). Matches on the raw `query` string rather than a resolved ИНН,
    since resolving it requires the very ЕГРЮЛ call the cache exists to avoid - querying
    once by name and again by ИНН for the same entity is a known miss, acceptable for
    Stage 1's simplicity. An `incomplete` scan (a required source failed) is never served
    from cache - a transient outage would otherwise stick for the whole TTL."""
    cutoff = datetime.datetime.now(datetime.UTC) - max_age
    result = await db.execute(
        select(RuBusinessCheckSearch)
        .where(
            RuBusinessCheckSearch.query == query,
            RuBusinessCheckSearch.status == "completed",
            RuBusinessCheckSearch.searched_at >= cutoff,
            or_(
                RuBusinessCheckSearch.risk_level.is_(None),
                RuBusinessCheckSearch.risk_level != "incomplete",
            ),
        )
        .order_by(RuBusinessCheckSearch.searched_at.desc())
        .limit(1)
    )
    return result.scalar_one_or_none()


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
