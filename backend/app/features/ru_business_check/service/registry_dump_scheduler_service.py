"""Recurring refresh + startup catch-up for the locally cached registry dumps
(disqualified persons, ЦБ warning list, OFAC SDN)."""

import datetime
import logging
from collections.abc import Awaitable, Callable
from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import managed_session
from app.core.scheduler import add_recurring_job, wrap_job_errors
from app.features.ru_business_check.service import (
    cbr_warning_service,
    disqualified_dump_service,
    ofac_sdn_service,
)
from app.features.ru_business_check.service.registry_dump_common import is_stale, refresh_lock

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class DumpJob:
    source: str
    name: str
    refresh: Callable[[AsyncSession], Awaitable[dict]]
    stale_after: datetime.timedelta
    interval_days: int

    @property
    def job_id(self) -> str:
        return f"ru_business_check_{self.source}_refresh"


def dump_jobs() -> list[DumpJob]:
    """Resolved at call time so tests can monkeypatch the refresh functions by name."""
    return [
        DumpJob(
            disqualified_dump_service.SOURCE_KEY,
            "disqualified-persons dump",
            disqualified_dump_service.refresh_dump,
            disqualified_dump_service.STALE_AFTER,
            7,
        ),
        DumpJob(
            cbr_warning_service.SOURCE_KEY,
            "ЦБ warning list",
            cbr_warning_service.refresh_list,
            cbr_warning_service.STALE_AFTER,
            2,
        ),
        DumpJob(
            ofac_sdn_service.SOURCE_KEY,
            "OFAC SDN list",
            ofac_sdn_service.refresh_list,
            ofac_sdn_service.STALE_AFTER,
            2,
        ),
    ]


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


async def refresh_dumps_if_stale() -> None:
    """Startup catch-up: a recurring job's countdown lives in memory and resets on every
    restart, so staleness is re-derived from the DB here (see the scheduler convention in
    AGENTS.md). A failure is logged, never fatal - a scan reports the source as not-checked."""
    for job in dump_jobs():
        try:
            await run_refresh(job, only_if_stale=True)
        except Exception as exc:
            logger.error("Background %s refresh failed: %s", job.name, exc)


def _scheduled(job: DumpJob) -> Callable[[], Awaitable[None]]:
    async def run() -> None:
        await run_refresh(job)

    return run


async def register_registry_dump_schedulers() -> None:
    for job in dump_jobs():
        add_recurring_job(
            job.job_id,
            wrap_job_errors(f"{job.name} refresh", _scheduled(job)),
            interval=job.interval_days,
            unit="days",
        )
