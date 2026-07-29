import logging

from app.core.database import managed_session
from app.core.scheduler import configure_recurring_job, is_scheduler_running, wrap_job_errors
from app.core.settings.username_search.crud.username_search_settings_crud import get_username_search_config
from app.features.username_search.service.db_refresh_service import refresh_database as refresh_maigret_database

logger = logging.getLogger(__name__)

MAIGRET_DB_REFRESH_JOB_ID = 'maigret_db_refresh'


async def _execute_maigret_db_refresh_job() -> None:
    async with managed_session() as db:
        config = await get_username_search_config(db)
        site_count = await refresh_maigret_database(db, check_interval_hours=config.auto_update_interval_hours)
    logger.debug("Maigret DB refresh job completed successfully: %s sites", site_count)


def configure_maigret_db_scheduler(enabled: bool, interval_hours: int) -> None:
    """Configure the Maigret site-database refresh scheduler with given parameters.

    Unlike configure_news_scheduler, a non-running scheduler is skipped here
    rather than bootstrapped, matching the old
    update_maigret_db_scheduler_configuration() behavior.
    """
    if not is_scheduler_running():
        logger.warning("Attempting to update non-running scheduler")
        return

    configure_recurring_job(
        MAIGRET_DB_REFRESH_JOB_ID,
        wrap_job_errors("Maigret DB refresh", _execute_maigret_db_refresh_job),
        enabled=enabled, interval=interval_hours, unit="hours",
    )


async def register_maigret_db_scheduler() -> None:
    """Initial registration at application startup."""
    async with managed_session() as db:
        config = await get_username_search_config(db)
    configure_recurring_job(
        MAIGRET_DB_REFRESH_JOB_ID,
        wrap_job_errors("Maigret DB refresh", _execute_maigret_db_refresh_job),
        enabled=config.auto_update_db_enabled, interval=config.auto_update_interval_hours, unit="hours",
    )
