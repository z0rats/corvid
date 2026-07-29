import logging
from typing import Any, Awaitable, Callable

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.jobstores.base import JobLookupError

from app.core.config.settings import settings

logger = logging.getLogger(__name__)

_scheduler: AsyncIOScheduler | None = None


def get_scheduler() -> AsyncIOScheduler:
    """Return the scheduler instance, creating it on first call within the running event loop."""
    global _scheduler
    if _scheduler is None:
        _scheduler = AsyncIOScheduler()
    return _scheduler


def remove_existing_job(job_id: str) -> None:
    """Remove a scheduler job if it exists."""
    try:
        get_scheduler().remove_job(job_id)
        logger.debug("Removed existing job: %s", job_id)
    except JobLookupError:
        logger.debug("No existing job found with ID: %s", job_id)


def add_recurring_job(
    job_id: str,
    coro: Callable[[], Awaitable[None]],
    *,
    interval: int,
    unit: str,
) -> None:
    """Add a recurring job to the scheduler with the given interval."""
    try:
        get_scheduler().add_job(
            coro,
            IntervalTrigger(**{unit: interval}),
            id=job_id,
            replace_existing=True,
            max_instances=settings.scheduler.max_job_instances,
        )
        logger.info("Job %s scheduled with %s %s interval", job_id, interval, unit)
    except Exception as e:
        logger.error("Error adding job %s: %s", job_id, e)
        raise


def configure_recurring_job(
    job_id: str,
    coro: Callable[[], Awaitable[None]],
    *,
    enabled: bool,
    interval: int,
    unit: str,
) -> None:
    """Reconfigure a recurring job: remove it, then re-add if enabled."""
    try:
        remove_existing_job(job_id)

        if enabled:
            add_recurring_job(job_id, coro, interval=interval, unit=unit)
            logger.info("Job %s enabled with %s %s interval", job_id, interval, unit)
        else:
            logger.info("Job %s disabled as per configuration", job_id)

    except Exception as e:
        logger.error("Error configuring job %s: %s", job_id, e)
        raise


def wrap_job_errors(
    job_name: str, coro_factory: Callable[[], Awaitable[Any]],
) -> Callable[[], Awaitable[None]]:
    """Wrap a coroutine factory so exceptions are logged and swallowed instead of removing the job from the scheduler."""
    async def _wrapped() -> None:
        try:
            await coro_factory()
        except Exception as e:
            logger.error("Error in %s job: %s", job_name, e)
    return _wrapped


def start_scheduler() -> None:
    """Start the scheduler if it isn't already running."""
    if not get_scheduler().running:
        get_scheduler().start()
        logger.info("Scheduler started successfully")
    else:
        logger.debug("Scheduler already running")


def is_scheduler_running() -> bool:
    return get_scheduler().running


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
