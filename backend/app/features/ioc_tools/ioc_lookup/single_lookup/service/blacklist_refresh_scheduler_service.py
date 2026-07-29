import logging

from app.core.config.settings import settings
from app.core.database import managed_session
from app.core.scheduler import add_recurring_job, wrap_job_errors
from app.features.ioc_tools.ioc_lookup.single_lookup.service.blacklist_refresh_service import refresh_blacklist

logger = logging.getLogger(__name__)

BLACKLIST_REFRESH_JOB_ID = 'blacklist_refresh'


async def _execute_blacklist_refresh_job() -> None:
    async with managed_session() as db:
        summary = await refresh_blacklist(db)
    logger.info("Blacklist refresh job completed: %s", summary)


async def register_blacklist_scheduler() -> None:
    """Initial registration at application startup.

    No configure_* counterpart: there is no UI toggle for the blacklist
    refresh interval, so it's added once with a fixed interval and never
    reconfigured.
    """
    add_recurring_job(
        BLACKLIST_REFRESH_JOB_ID,
        wrap_job_errors("blacklist refresh", _execute_blacklist_refresh_job),
        interval=settings.scheduler.blacklist_refresh_interval_hours, unit="hours",
    )
