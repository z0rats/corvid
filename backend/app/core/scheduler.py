import logging
from typing import Any

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.jobstores.base import JobLookupError

from app.core.config.settings import settings
from app.core.database import managed_session
from app.features.newsfeed.crud.newsfeed_config_crud import get_newsfeed_config
from app.features.newsfeed.service.feed_processing_service import fetch_and_store_news
from app.features.ioc_tools.ioc_lookup.single_lookup.service.blacklist_refresh_service import refresh_blacklist
from app.core.settings.username_search.crud.username_search_settings_crud import get_username_search_config
from app.features.username_search.service.db_refresh_service import refresh_database as refresh_maigret_database

logger = logging.getLogger(__name__)

NEWS_FETCH_JOB_ID = 'news_fetch'
BLACKLIST_REFRESH_JOB_ID = 'blacklist_refresh'
MAIGRET_DB_REFRESH_JOB_ID = 'maigret_db_refresh'

_scheduler: AsyncIOScheduler | None = None


def get_scheduler() -> AsyncIOScheduler:
    """Return the scheduler instance, creating it on first call within the running event loop."""
    global _scheduler
    if _scheduler is None:
        _scheduler = AsyncIOScheduler()
    return _scheduler


async def execute_news_fetch_job() -> None:
    """Execute news fetching with error handling to prevent scheduler job removal."""
    try:
        async with managed_session() as db:
            await fetch_and_store_news(db)
        logger.debug("News fetch job completed successfully")
    except Exception as e:
        logger.error("Error in news fetch job: %s", e)


async def execute_blacklist_refresh_job() -> None:
    """Execute the address blacklist refresh with error handling to prevent scheduler job removal."""
    try:
        async with managed_session() as db:
            summary = await refresh_blacklist(db)
        logger.info("Blacklist refresh job completed: %s", summary)
    except Exception as e:
        logger.error("Error in blacklist refresh job: %s", e)


def add_blacklist_refresh_job(interval_hours: int) -> None:
    """Add the address blacklist refresh job to the scheduler with the given interval."""
    try:
        get_scheduler().add_job(
            execute_blacklist_refresh_job,
            IntervalTrigger(hours=interval_hours),
            id=BLACKLIST_REFRESH_JOB_ID,
            replace_existing=True,
            max_instances=settings.scheduler.max_job_instances
        )
        logger.info("Blacklist refresh job scheduled with %s hour interval", interval_hours)
    except Exception as e:
        logger.error("Error adding blacklist refresh job: %s", e)
        raise


async def execute_maigret_db_refresh_job() -> None:
    """Execute the Maigret site-database refresh with error handling to prevent scheduler job removal."""
    try:
        async with managed_session() as db:
            config = await get_username_search_config(db)
            site_count = await refresh_maigret_database(db, check_interval_hours=config.auto_update_interval_hours)
        logger.debug("Maigret DB refresh job completed successfully: %s sites", site_count)
    except Exception as e:
        logger.error("Error in Maigret DB refresh job: %s", e)


def add_maigret_db_refresh_job(interval_hours: int) -> None:
    """Add the Maigret site-database refresh job to the scheduler with the given interval."""
    try:
        get_scheduler().add_job(
            execute_maigret_db_refresh_job,
            IntervalTrigger(hours=interval_hours),
            id=MAIGRET_DB_REFRESH_JOB_ID,
            replace_existing=True,
            max_instances=settings.scheduler.max_job_instances
        )
        logger.info("Maigret DB refresh job scheduled with %s hour interval", interval_hours)
    except Exception as e:
        logger.error("Error adding Maigret DB refresh job: %s", e)
        raise


def configure_maigret_db_scheduler(enabled: bool, interval_hours: int) -> None:
    """Configure the Maigret site-database refresh scheduler with given parameters."""
    try:
        remove_existing_job(MAIGRET_DB_REFRESH_JOB_ID)

        if enabled:
            add_maigret_db_refresh_job(interval_hours)
            logger.info("Maigret DB refresh scheduler enabled with %s hour interval", interval_hours)
        else:
            logger.info("Maigret DB refresh scheduler disabled as per configuration")

    except Exception as e:
        logger.error("Error configuring Maigret DB refresh scheduler: %s", e)
        raise


async def update_maigret_db_scheduler_configuration() -> None:
    """Update the Maigret DB refresh scheduler with new configuration from database."""
    try:
        if not get_scheduler().running:
            logger.warning("Attempting to update non-running scheduler")
            return

        async with managed_session() as db:
            config = await get_username_search_config(db)
        configure_maigret_db_scheduler(config.auto_update_db_enabled, config.auto_update_interval_hours)
        logger.info("Maigret DB refresh scheduler configuration updated successfully")

    except Exception as e:
        logger.error("Failed to update Maigret DB refresh scheduler configuration: %s", e)
        raise


async def fetch_scheduler_configuration() -> tuple[bool, int]:
    """Retrieve scheduler configuration from database."""
    try:
        async with managed_session() as db:
            config = await get_newsfeed_config(db=db)
            return config.background_fetch_enabled, config.fetch_interval_minutes
    except Exception as e:
        logger.error("Error fetching scheduler config: %s", e)
        return False, settings.scheduler.default_fetch_interval


def remove_existing_job(job_id: str) -> None:
    """Remove a scheduler job if it exists."""
    try:
        get_scheduler().remove_job(job_id)
        logger.debug("Removed existing job: %s", job_id)
    except JobLookupError:
        logger.debug("No existing job found with ID: %s", job_id)


def add_news_fetch_job(interval_minutes: int) -> None:
    """Add news fetching job to scheduler with the given interval."""
    try:
        get_scheduler().add_job(
            execute_news_fetch_job,
            IntervalTrigger(minutes=interval_minutes),
            id=NEWS_FETCH_JOB_ID,
            replace_existing=True,
            max_instances=settings.scheduler.max_job_instances
        )
        logger.info("News fetch job scheduled with %s minute interval", interval_minutes)
    except Exception as e:
        logger.error("Error adding news fetch job: %s", e)
        raise


def configure_news_scheduler(enabled: bool, interval_minutes: int) -> None:
    """Configure news fetching scheduler with given parameters."""
    try:
        remove_existing_job(NEWS_FETCH_JOB_ID)

        if enabled:
            add_news_fetch_job(interval_minutes)
            logger.info("News scheduler enabled with %s minute interval", interval_minutes)
        else:
            logger.info("News scheduler disabled as per configuration")

    except Exception as e:
        logger.error("Error configuring news scheduler: %s", e)
        raise


async def initialize_scheduler() -> None:
    """Initialize and start the scheduler with database configuration."""
    try:
        enabled, interval = await fetch_scheduler_configuration()
        configure_news_scheduler(enabled, interval)
        add_blacklist_refresh_job(settings.scheduler.blacklist_refresh_interval_hours)

        async with managed_session() as db:
            username_search_config = await get_username_search_config(db)
        configure_maigret_db_scheduler(
            username_search_config.auto_update_db_enabled,
            username_search_config.auto_update_interval_hours,
        )

        if not get_scheduler().running:
            get_scheduler().start()
            logger.info("Scheduler started successfully")
        else:
            logger.debug("Scheduler already running")

    except Exception as e:
        logger.error("Failed to initialize scheduler: %s", e)
        raise


async def update_scheduler_configuration() -> None:
    """Update scheduler with new configuration from database."""
    try:
        if not get_scheduler().running:
            logger.warning("Attempting to update non-running scheduler")
            await initialize_scheduler()
            return

        enabled, interval = await fetch_scheduler_configuration()
        configure_news_scheduler(enabled, interval)
        logger.info("Scheduler configuration updated successfully")

    except Exception as e:
        logger.error("Failed to update scheduler configuration: %s", e)
        raise


def stop_scheduler(wait_for_jobs: bool = True) -> None:
    """Safely shutdown the scheduler."""
    try:
        if get_scheduler().running:
            get_scheduler().shutdown(wait=wait_for_jobs)
            logger.info("Scheduler shutdown successfully")
        else:
            logger.debug("Scheduler already stopped")

    except Exception as e:
        logger.error("Error during scheduler shutdown: %s", e)
        raise


def get_scheduler_status() -> dict[str, Any]:
    """Get current scheduler status and job information."""
    try:
        scheduler = get_scheduler()
        is_running = scheduler.running
        jobs = []

        if is_running:
            for job in scheduler.get_jobs():
                jobs.append({
                    "id": job.id,
                    "name": job.name or "Unnamed Job",
                    "next_run": job.next_run_time.isoformat() if job.next_run_time else None
                })

        return {
            "running": is_running,
            "job_count": len(jobs),
            "jobs": jobs
        }

    except Exception as e:
        logger.error("Error getting scheduler status: %s", e)
        return {
            "running": False,
            "job_count": 0,
            "jobs": [],
            "error": str(e)
        }
