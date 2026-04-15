import logging
from typing import Any

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.jobstores.base import JobLookupError

from app.core.config.settings import settings
from app.core.database import managed_session
from app.features.newsfeed.crud.newsfeed_config_crud import get_newsfeed_config
from app.features.newsfeed.service.feed_processing_service import fetch_and_store_news

logger = logging.getLogger(__name__)

NEWS_FETCH_JOB_ID = 'news_fetch'

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
