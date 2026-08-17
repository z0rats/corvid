import asyncio
import logging

import httpx

from app.core.scans.cancellable import TaskCancellable
from app.core.scans.run import ScanCancelled, ScanOutcome, ScanRun
from app.core.scans.sse import queue_sink
from app.features.username_search.crud.username_search_crud import SCAN_COLUMNS, add_site_results
from app.features.username_search.models.username_search_models import MaigretSearch

logger = logging.getLogger(__name__)

FEATURE_NAME = "threat_actor_usernames"

BASE_URL = "https://threatactorusernames.com"
REQUEST_TIMEOUT_SECONDS = 10.0


async def cancel_scan(search_id: int) -> bool:
    """Request cancellation of a currently-running lookup. Returns False if
    no scan with that id is currently running (already finished, or never existed)."""
    return await ScanRun.cancel(FEATURE_NAME, search_id)


def _extract_found_sites(results: list[dict]) -> list[dict]:
    """Build the list of found-site rows to persist from the API's raw results list.

    Unlike Maigret/social-analyzer there's no profile URL to link to - the API
    only reports which forum a username was scraped from - so url_user is left
    empty and the matched username/logo are kept in `extra` instead.
    """
    found_sites = []
    for item in results:
        found_sites.append(
            {
                "site_name": item.get("forum", ""),
                "url_user": "",
                "http_status": None,
                "extra": {"username": item.get("username"), "logo": item.get("logo")},
            }
        )
    return found_sites


async def run_scan(username: str, queue: asyncio.Queue) -> None:
    """Look up a username against threatactorusernames.com's public API - a
    prebuilt index of usernames scraped from cybercrime/threat-actor forums -
    persisting the result and streaming start/completion events.

    Unlike Maigret/social-analyzer this is a single API call, not a per-site
    scan, so there's no per-site progress - just a "started" event followed by
    one terminal event.
    """
    on_event = queue_sink(queue)

    async def run_work(search_id: int) -> ScanOutcome:
        try:
            async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT_SECONDS) as client:
                response = await client.get(f"{BASE_URL}/api/search", params={"q": username})
                response.raise_for_status()
                data = response.json()
        except asyncio.CancelledError:
            raise ScanCancelled(
                ScanOutcome(
                    fields={"total_sites_checked": 0, "found_count": 0},
                    persist_children=lambda db: add_site_results(db, search_id, []),
                )
            ) from None
        except (httpx.HTTPError, ValueError) as exc:
            # Not logged here - ScanRun.execute()'s own generic exception handler
            # already logs every run_work failure once, with feature/search_id context.
            raise RuntimeError(f"Threat Actor Username Search lookup failed: {exc}") from exc

        found_sites = _extract_found_sites(data.get("results", []))

        return ScanOutcome(
            fields={"total_sites_checked": len(found_sites), "found_count": len(found_sites)},
            persist_children=lambda db: add_site_results(db, search_id, found_sites),
        )

    cancellable = TaskCancellable(asyncio.current_task())
    await ScanRun.execute(
        FEATURE_NAME,
        MaigretSearch,
        run_work,
        on_event,
        columns=SCAN_COLUMNS,
        create_fields={"username": username, "source": "threat_actor_usernames"},
        started_fields={"username": username, "total_sites": None},
        cancellable=cancellable,
    )
