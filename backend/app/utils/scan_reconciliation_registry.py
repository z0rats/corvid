import logging

from app.core.database import managed_session
from app.features.amass.crud.amass_crud import AMASS_SCANS
from app.features.email_search.crud.email_search_crud import EMAIL_SEARCH_SCANS
from app.features.git_recon.crud.git_recon_crud import GIT_RECON_SCANS
from app.features.instagram_search.crud.instagram_search_crud import INSTAGRAM_SCANS
from app.features.phone_search.crud.phone_search_crud import PHONE_SEARCH_SCANS
from app.features.ru_business_check.crud.ru_business_check_crud import RU_BUSINESS_CHECK_SCANS
from app.features.steam_recon.crud.steam_recon_crud import STEAM_RECON_SCANS
from app.features.username_search.crud.username_search_crud import USERNAME_SEARCH_SCANS

logger = logging.getLogger(__name__)

# Every scan feature's `ScanFeature` (one per scan table). The only place allowed to know
# about all scan features at once - see router_registry.py/scheduler_registry.py for the
# same pattern applied to routers/scheduler jobs. Covered by
# tests/core/test_scan_reconciliation_coverage.py, which fails if a feature declares a
# `ScanFeature` without registering it here.
_SCAN_FEATURES = [
    USERNAME_SEARCH_SCANS,
    EMAIL_SEARCH_SCANS,
    PHONE_SEARCH_SCANS,
    GIT_RECON_SCANS,
    RU_BUSINESS_CHECK_SCANS,
    AMASS_SCANS,
    STEAM_RECON_SCANS,
    INSTAGRAM_SCANS,
]


async def reconcile_stale_scans() -> None:
    """Mark every scan feature's runs still 'running' from a previous process as failed.

    Each scan is driven by a detached `asyncio.create_task()` (see the relevant
    `routers/*_routes.py` `scan`/`start_scan` handler) that outlives the SSE request but not
    the process itself, so a container stop/crash mid-scan leaves the row stuck at 'running'
    with nothing to ever move it out of that state.
    """
    async with managed_session() as db:
        reconciled = [
            (feature.name, await feature.interrupt_running(db)) for feature in _SCAN_FEATURES
        ]

    nonzero = [(name, count) for name, count in reconciled if count]
    if nonzero:
        logger.info(
            "Reconciled stale scan runs left 'running' by a previous process: %s",
            ", ".join(f"{count} {name}" for name, count in nonzero),
        )
