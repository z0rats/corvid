"""Generic recurring-refresh + startup-catch-up engine for locally cached registry dumps.
Each feature that owns one or more dumps (`ru_business_check`'s disqualified-persons dump, ЦБ
warning list, OFAC SDN; `sanctions_search`'s OpenSanctions mirror; ...) keeps its own small
`dump_jobs()`/`register_*_scheduler()` wrapper naming its own `DumpJob`s, and calls into the
functions here rather than reimplementing the no-overlap/lock-spans-commit/stale-on-restart
logic itself."""

import datetime
import logging
from collections.abc import Awaitable, Callable
from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import managed_session
from app.core.registry_dumps.common import is_stale, refresh_lock
from app.core.scheduler import add_recurring_job, wrap_job_errors

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class DumpJob:
    source: str
    name: str
    refresh: Callable[[AsyncSession], Awaitable[dict]]
    stale_after: datetime.timedelta
    interval_days: int
    prefix: str  # scheduler job-id namespace, e.g. "ru_business_check", "sanctions_search"

    @property
    def job_id(self) -> str:
        return f"{self.prefix}_{self.source}_refresh"


async def run_refresh(job: DumpJob, *, only_if_stale: bool = False) -> dict | None:
    """Refresh one dump under its lock, which covers the whole transaction including the
    commit (see `refresh_lock`). A refresh already in progress for the same source - the
    startup catch-up and the scheduled job can fire together - makes this one a no-op
    rather than queueing a second full download. Returns the summary, or None if skipped."""
    lock = refresh_lock(job.source)
    if lock.locked():
        logger.info("%s refresh already in progress; skipping", job.name)
        return None
    async with lock:
        async with managed_session() as db:
            if only_if_stale and not await is_stale(db, job.source, job.stale_after):
                return None
            if only_if_stale:
                logger.info("%s is missing or stale; refreshing", job.name)
            summary = await job.refresh(db)
    logger.info("%s refresh completed: %s", job.name, summary)
    return summary


async def refresh_jobs_if_stale(jobs: list[DumpJob]) -> None:
    """Startup catch-up: a recurring job's countdown lives in memory and resets on every
    restart, so staleness is re-derived from the DB here (see the scheduler convention in
    AGENTS.md). A failure is logged, never fatal - a lookup reports the source as not-checked."""
    for job in jobs:
        try:
            await run_refresh(job, only_if_stale=True)
        except Exception as exc:
            logger.error("Background %s refresh failed: %s", job.name, exc)


def _scheduled(job: DumpJob) -> Callable[[], Awaitable[None]]:
    async def run() -> None:
        await run_refresh(job)

    return run


def register_jobs(jobs: list[DumpJob]) -> None:
    for job in jobs:
        add_recurring_job(
            job.job_id,
            wrap_job_errors(f"{job.name} refresh", _scheduled(job)),
            interval=job.interval_days,
            unit="days",
        )
