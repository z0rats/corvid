import asyncio
import logging

import httpx

from app.core.database import managed_session
from app.core.scans.cancellable import TaskCancellable
from app.core.scans.run import ScanCancelled, ScanEvent, ScanOutcome, ScanRun
from app.core.scans.sse import queue_sink
from app.core.settings.phone_search.crud.phone_search_settings_crud import get_phone_search_config
from app.features.phone_search.config.checkers_config import get_active_checkers
from app.features.phone_search.crud.phone_search_crud import SCAN_COLUMNS, add_provider_results
from app.features.phone_search.models.phone_search_models import PhoneSearch

logger = logging.getLogger(__name__)

FEATURE_NAME = "phone_search"

# A realistic desktop-browser User-Agent - best-effort only, no TLS/JA3
# fingerprint spoofing, so these checkers are more easily bot-detected than a
# real browser. See the checker modules' own docstrings for the tradeoff.
_USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
)


async def cancel_scan(search_id: int) -> bool:
    """Request cancellation of a currently-running scan. Returns False if
    no scan with that id is currently running (already finished, or never existed)."""
    return await ScanRun.cancel(FEATURE_NAME, search_id)


async def _run_checker(
    checker, phone_number: str, client: httpx.AsyncClient, timeout: float
) -> dict:
    """Run a single phone-search checker module, mapping its result/any
    exception onto a uniform dict - mirrors email_search's `_run_checker`."""
    provider_name = checker.PROVIDER_NAME
    try:
        found = await asyncio.wait_for(
            checker.check(phone_number, client, timeout), timeout=timeout + 0.5
        )
        return {"provider_name": provider_name, "found": found, "error": None}
    except Exception as exc:
        logger.debug("Checker %s failed for the searched phone number: %s", provider_name, exc)
        return {"provider_name": provider_name, "found": False, "error": str(exc)}


async def run_scan(phone_number: str, queue: asyncio.Queue) -> None:
    """Run a phone-number registration search across the active checkers,
    persisting the result and streaming live progress via the given queue.

    Runs independently of the SSE client's connection: spawned as a background
    task by the route handler, it keeps running and persists its result even
    if the client disconnects mid-scan. It can be cancelled from another
    request via `cancel_scan(search_id)`.
    """
    on_event = queue_sink(queue)

    async with managed_session() as db:
        config = await get_phone_search_config(db)
        timeout_seconds = config.timeout_seconds
        proxy_url = config.proxy_url

    checkers = get_active_checkers()
    client = httpx.AsyncClient(
        headers={"User-Agent": _USER_AGENT}, follow_redirects=True, proxy=proxy_url or None
    )

    async def run_work(search_id: int) -> ScanOutcome:
        checked = 0
        found_providers: list[dict] = []
        tasks = [
            asyncio.ensure_future(_run_checker(checker, phone_number, client, timeout_seconds))
            for checker in checkers
        ]
        try:
            for task in asyncio.as_completed(tasks):
                result = await task
                checked += 1
                if result["found"]:
                    found_providers.append({"provider_name": result["provider_name"]})
                on_event(
                    ScanEvent(
                        "progress",
                        {
                            "checked": checked,
                            "total_providers": len(checkers),
                            "provider_name": result["provider_name"],
                            "found": result["found"],
                        },
                    )
                )
        except asyncio.CancelledError:
            for task in tasks:
                task.cancel()
            raise ScanCancelled(
                ScanOutcome(
                    fields={
                        "total_providers_checked": checked,
                        "found_count": len(found_providers),
                    },
                    persist_children=lambda db: add_provider_results(
                        db, search_id, found_providers
                    ),
                )
            ) from None

        return ScanOutcome(
            fields={"total_providers_checked": len(checkers), "found_count": len(found_providers)},
            persist_children=lambda db: add_provider_results(db, search_id, found_providers),
        )

    cancellable = TaskCancellable(asyncio.current_task())
    try:
        await ScanRun.execute(
            FEATURE_NAME,
            PhoneSearch,
            run_work,
            on_event,
            columns=SCAN_COLUMNS,
            create_fields={"phone_number": phone_number},
            started_fields={"phone_number": phone_number, "total_providers": len(checkers)},
            cancellable=cancellable,
        )
    finally:
        await client.aclose()
