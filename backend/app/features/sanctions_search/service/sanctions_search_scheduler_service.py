"""Recurring refresh + startup catch-up for the OpenSanctions/OFAC SDN mirror - a thin wrapper
naming this feature's one job around the generic engine in app.core.registry_dumps.scheduler
(same pattern as ru_business_check's registry_dump_scheduler_service.py)."""

from app.core.registry_dumps.scheduler import DumpJob, refresh_jobs_if_stale, register_jobs
from app.features.sanctions_search.service import sanctions_search_service


def dump_jobs() -> list[DumpJob]:
    return [
        DumpJob(
            sanctions_search_service.SOURCE_KEY,
            "OpenSanctions/OFAC SDN list",
            sanctions_search_service.refresh_list,
            sanctions_search_service.STALE_AFTER,
            2,
            prefix="sanctions_search",
        ),
    ]


async def refresh_sanctions_search_dumps_if_stale() -> None:
    await refresh_jobs_if_stale(dump_jobs())


async def register_sanctions_search_scheduler() -> None:
    register_jobs(dump_jobs())
