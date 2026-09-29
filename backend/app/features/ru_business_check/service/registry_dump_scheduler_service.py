"""Recurring refresh + startup catch-up for ru_business_check's locally cached registry dumps
(disqualified persons, ЦБ warning list, OFAC SDN) - a thin wrapper naming this feature's jobs
around the generic engine in `app.core.registry_dumps.scheduler`."""

from app.core.registry_dumps.scheduler import DumpJob, refresh_jobs_if_stale, register_jobs
from app.features.ru_business_check.service import (
    cbr_warning_service,
    disqualified_dump_service,
    ofac_sdn_service,
)


def dump_jobs() -> list[DumpJob]:
    """Resolved at call time so tests can monkeypatch the refresh functions by name."""
    return [
        DumpJob(
            disqualified_dump_service.SOURCE_KEY,
            "disqualified-persons dump",
            disqualified_dump_service.refresh_dump,
            disqualified_dump_service.STALE_AFTER,
            7,
            prefix="ru_business_check",
        ),
        DumpJob(
            cbr_warning_service.SOURCE_KEY,
            "ЦБ warning list",
            cbr_warning_service.refresh_list,
            cbr_warning_service.STALE_AFTER,
            2,
            prefix="ru_business_check",
        ),
        DumpJob(
            ofac_sdn_service.SOURCE_KEY,
            "OFAC SDN list",
            ofac_sdn_service.refresh_list,
            ofac_sdn_service.STALE_AFTER,
            2,
            prefix="ru_business_check",
        ),
    ]


async def refresh_dumps_if_stale() -> None:
    """Startup catch-up: a recurring job's countdown lives in memory and resets on every
    restart, so staleness is re-derived from the DB (see the scheduler convention in
    AGENTS.md)."""
    await refresh_jobs_if_stale(dump_jobs())


async def register_registry_dump_schedulers() -> None:
    register_jobs(dump_jobs())
