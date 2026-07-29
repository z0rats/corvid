import logging

from app.core.config.settings import settings
from app.core.database import managed_session
from app.core.scheduler import configure_recurring_job, is_scheduler_running, start_scheduler, wrap_job_errors
from app.features.newsfeed.crud.newsfeed_config_crud import get_newsfeed_config
from app.features.newsfeed.service.feed_processing_service import fetch_and_store_news

logger = logging.getLogger(__name__)

NEWS_FETCH_JOB_ID = 'news_fetch'


async def _execute_news_fetch_job() -> None:
    async with managed_session() as db:
        await fetch_and_store_news(db)
    logger.debug("News fetch job completed successfully")


def configure_news_scheduler(enabled: bool, interval_minutes: int) -> None:
    """Configure news fetching scheduler with given parameters.

    Unlike configure_maigret_db_scheduler, a non-running scheduler is
    bootstrapped here rather than skipped, matching the old
    update_scheduler_configuration() behavior.
    """
    if not is_scheduler_running():
        logger.warning("Attempting to update non-running scheduler; bootstrapping")
        start_scheduler()

    configure_recurring_job(
        NEWS_FETCH_JOB_ID,
        wrap_job_errors("news fetch", _execute_news_fetch_job),
        enabled=enabled, interval=interval_minutes, unit="minutes",
    )


def _register_news_fetch_job(enabled: bool, interval_minutes: int) -> None:
    configure_recurring_job(
        NEWS_FETCH_JOB_ID,
        wrap_job_errors("news fetch", _execute_news_fetch_job),
        enabled=enabled, interval=interval_minutes, unit="minutes",
    )


async def register_newsfeed_scheduler() -> None:
    """Initial registration at application startup.

    Registers directly via configure_recurring_job rather than
    configure_news_scheduler, since the scheduler isn't running yet at this
    point (start_scheduler() runs after all features register their jobs).
    """
    try:
        async with managed_session() as db:
            config = await get_newsfeed_config(db=db)
        _register_news_fetch_job(config.background_fetch_enabled, config.fetch_interval_minutes)
    except Exception as e:
        logger.error("Error fetching scheduler config: %s", e)
        _register_news_fetch_job(False, settings.scheduler.default_fetch_interval)
