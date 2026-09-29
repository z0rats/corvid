import logging

from app.core.database import managed_session
from app.features.amass.crud.amass_crud import interrupt_running_searches as _interrupt_amass
from app.features.email_search.crud.email_search_crud import (
    interrupt_running_searches as _interrupt_email_search,
)
from app.features.git_recon.crud.git_recon_crud import (
    interrupt_running_searches as _interrupt_git_recon,
)
from app.features.instagram_search.crud.instagram_search_crud import (
    interrupt_running_searches as _interrupt_instagram_search,
)
from app.features.phone_search.crud.phone_search_crud import (
    interrupt_running_searches as _interrupt_phone_search,
)
from app.features.ru_business_check.crud.ru_business_check_crud import (
    interrupt_running_searches as _interrupt_ru_business_check,
)
from app.features.steam_recon.crud.steam_recon_crud import (
    interrupt_running_searches as _interrupt_steam_recon,
)
from app.features.username_search.crud.username_search_crud import (
    interrupt_running_searches as _interrupt_username_search,
)

logger = logging.getLogger(__name__)

# Every scan-style feature's own `interrupt_running_searches(db) -> int`, paired with the
# display name used in the reconciliation log line. The only place allowed to know about all
# scan features at once - see router_registry.py/scheduler_registry.py for the same pattern
# applied to routers/scheduler jobs. Covered by tests/core/test_scan_reconciliation_coverage.py,
# which fails if a feature adds `interrupt_running_searches` to its crud module without also
# registering it here.
_SCAN_FEATURES = [
    ("username-search", _interrupt_username_search),
    ("email-search", _interrupt_email_search),
    ("phone-search", _interrupt_phone_search),
    ("git-recon", _interrupt_git_recon),
    ("ru-business-check", _interrupt_ru_business_check),
    ("amass", _interrupt_amass),
    ("steam-recon", _interrupt_steam_recon),
    ("instagram-search", _interrupt_instagram_search),
]


async def reconcile_stale_scans() -> None:
    """Mark every scan-style feature's search runs still 'running' from a previous process
    as failed.

    Each scan is driven by a detached `asyncio.create_task()` (see the relevant
    `routers/*_routes.py` `scan`/`start_scan` handler) that outlives the SSE request but not
    the process itself, so a container stop/crash mid-scan leaves the row stuck at 'running'
    with nothing to ever move it out of that state.
    """
    async with managed_session() as db:
        reconciled = [(name, await interrupt_fn(db)) for name, interrupt_fn in _SCAN_FEATURES]

    nonzero = [(name, count) for name, count in reconciled if count]
    if nonzero:
        logger.info(
            "Reconciled stale scan runs left 'running' by a previous process: %s",
            ", ".join(f"{count} {name}" for name, count in nonzero),
        )
