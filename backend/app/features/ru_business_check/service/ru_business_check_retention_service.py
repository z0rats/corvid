import logging

from app.core.database import managed_session
from app.core.scheduler import add_recurring_job, wrap_job_errors
from app.core.settings.ru_business_check.crud.ru_business_check_settings_crud import (
    get_ru_business_check_settings,
)
from app.features.ru_business_check.crud.ru_business_check_crud import delete_expired_searches

logger = logging.getLogger(__name__)

RETENTION_SWEEP_JOB_ID = "ru_business_check_retention_sweep"
RETENTION_SWEEP_INTERVAL_HOURS = 24


async def _run_retention_sweep() -> None:
    async with managed_session() as db:
        settings_row = await get_ru_business_check_settings(db)
        deleted = await delete_expired_searches(db, settings_row.history_retention_days)
    if deleted:
        logger.info("ru_business_check retention sweep deleted %d expired search(es)", deleted)


async def register_ru_business_check_retention_scheduler() -> None:
    """Register the daily sweep that deletes searches (and their raw scraped payloads)
    older than the configured `history_retention_days` - the actual deletion half of the
    TTL decision (retention_days alone, without this, would only ever be documentation)."""
    add_recurring_job(
        RETENTION_SWEEP_JOB_ID,
        wrap_job_errors("ru_business_check retention sweep", _run_retention_sweep),
        interval=RETENTION_SWEEP_INTERVAL_HOURS,
        unit="hours",
    )
