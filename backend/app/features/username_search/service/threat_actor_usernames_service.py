import asyncio
import logging

import httpx

from app.core.database import managed_session
from app.features.username_search.crud.username_search_crud import (
    cancel_search_run,
    complete_search_run,
    create_search_run,
    fail_search_run,
)

logger = logging.getLogger(__name__)

BASE_URL = "https://threatactorusernames.com"
REQUEST_TIMEOUT_SECONDS = 10.0

# In-memory registry of currently-running lookups, keyed by search_id, mirroring
# username_search_service's registry - kept separate since this is a distinct
# source with its own cancel_scan().
_active_scans: dict[int, asyncio.Task] = {}


def cancel_scan(search_id: int) -> bool:
    """Request cancellation of a currently-running lookup. Returns False if
    no scan with that id is currently running (already finished, or never existed)."""
    task = _active_scans.get(search_id)
    if task is None or task.done():
        return False
    task.cancel()
    return True


def _extract_found_sites(results: list[dict]) -> list[dict]:
    """Build the list of found-site rows to persist from the API's raw results list.

    Unlike Maigret/social-analyzer there's no profile URL to link to - the API
    only reports which forum a username was scraped from - so url_user is left
    empty and the matched username/logo are kept in `extra` instead.
    """
    found_sites = []
    for item in results:
        found_sites.append({
            "site_name": item.get("forum", ""),
            "url_user": "",
            "http_status": None,
            "extra": {"username": item.get("username"), "logo": item.get("logo")},
        })
    return found_sites


async def run_scan(username: str, queue: asyncio.Queue) -> None:
    """Look up a username against threatactorusernames.com's public API - a
    prebuilt index of usernames scraped from cybercrime/threat-actor forums -
    persisting the result and streaming start/completion events.

    Unlike Maigret/social-analyzer this is a single API call, not a per-site
    scan, so there's no per-site progress - just a "started" event followed by
    one terminal event.
    """
    async with managed_session() as db:
        search = await create_search_run(db, username, source="threat_actor_usernames")
        search_id = search.id

    _active_scans[search_id] = asyncio.current_task()

    queue.put_nowait({
        "type": "started",
        "search_id": search_id,
        "username": username,
        "total_sites": None,
    })

    try:
        try:
            async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT_SECONDS) as client:
                response = await client.get(f"{BASE_URL}/api/search", params={"q": username})
                response.raise_for_status()
                data = response.json()
        except asyncio.CancelledError:
            async with managed_session() as db:
                await cancel_search_run(db, search_id, total_sites_checked=0, found_sites=[])
            queue.put_nowait({
                "type": "cancelled", "search_id": search_id, "total_sites_checked": 0, "found_count": 0,
            })
            queue.put_nowait(None)
            raise
        except (httpx.HTTPError, ValueError) as exc:
            error = f"Threat Actor Username Search lookup failed: {exc}"
            logger.error("%s ('%s')", error, username)
            async with managed_session() as db:
                await fail_search_run(db, search_id, error)
            queue.put_nowait({"type": "failed", "search_id": search_id, "error": error})
            queue.put_nowait(None)
            return

        found_sites = _extract_found_sites(data.get("results", []))

        async with managed_session() as db:
            await complete_search_run(db, search_id, total_sites_checked=len(found_sites), found_sites=found_sites)

        queue.put_nowait({
            "type": "completed",
            "search_id": search_id,
            "total_sites_checked": len(found_sites),
            "found_count": len(found_sites),
        })
        queue.put_nowait(None)
    finally:
        _active_scans.pop(search_id, None)
