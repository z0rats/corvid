import asyncio
import logging

from maigret.checking import maigret as run_maigret_checks

from app.core.database import managed_session
from app.core.settings.username_search.crud.username_search_settings_crud import get_username_search_config
from app.features.username_search.config.maigret_config import get_site_dict
from app.features.username_search.crud.username_search_crud import (
    cancel_search_run,
    complete_search_run,
    create_search_run,
    fail_search_run,
)
from app.features.username_search.service.report_service import save_scan_results

logger = logging.getLogger(__name__)

# In-memory registry of currently-running scan tasks, keyed by search_id, so a
# separate request can reach back in and cancel one. Process-local is fine
# here (single-user, single-process self-hosted app).
_active_scans: dict[int, asyncio.Task] = {}


def cancel_scan(search_id: int) -> bool:
    """Request cancellation of a currently-running scan. Returns False if
    no scan with that id is currently running (already finished, or never existed)."""
    task = _active_scans.get(search_id)
    if task is None or task.done():
        return False
    task.cancel()
    return True


class StreamingQueryNotify:
    """Forwards Maigret's per-site progress to an asyncio.Queue as plain dict
    events, in place of Maigret's own terminal-printing notifier. Consumed by
    the SSE route handler to stream live "CLI-style" progress to the client.
    """

    def __init__(self, queue: asyncio.Queue, total_sites: int):
        self.queue = queue
        self.total_sites = total_sites
        self.checked = 0

    def start(self, message=None, id_type="username"):
        # No-op: the route's "started" event (with search_id) is pushed by
        # run_scan() itself before this notifier is even created, so the
        # frontend has a search_id to cancel by from the very first event.
        pass

    def update(self, result, is_similar=False):
        self.checked += 1
        event = {
            "type": "progress",
            "checked": self.checked,
            "total_sites": self.total_sites,
            "site_name": result.site_name,
            # "claimed", "available", "unknown" (check failed/blocked), or "illegal"
            # - kept distinct (not just a found/not-found bool) so the UI can show
            # blocked/error checks differently from genuine not-found, like the CLI does.
            "status": result.status.value.lower(),
            "found": result.is_found(),
        }
        if result.is_found():
            event["url_user"] = result.site_url_user
        self.queue.put_nowait(event)

    def warning(self, message, symbol="-", advice=None):
        pass

    def finish(self, message=None):
        pass


def _extract_found_sites(results: dict) -> list[dict]:
    """Build the list of found-site rows to persist from Maigret's raw results dict"""
    found_sites = []
    for site_name, site_result in results.items():
        status = site_result.get("status")
        if status is None or not status.is_found():
            continue
        http_status = site_result.get("http_status")
        found_sites.append({
            "site_name": site_name,
            "url_user": site_result.get("url_user", ""),
            "http_status": http_status if isinstance(http_status, int) else None,
        })
    return found_sites


async def run_scan(
    username: str,
    queue: asyncio.Queue,
    tags: list[str] | None = None,
    excluded_tags: list[str] | None = None,
) -> None:
    """Run a full Maigret username search, persisting the result and streaming
    live progress via the given queue.

    Runs independently of the SSE client's connection: spawned as a background
    task by the route handler, it keeps running and persists its result even
    if the client disconnects mid-scan. It can be cancelled from another
    request via `cancel_scan(search_id)`.
    """
    async with managed_session() as db:
        config = await get_username_search_config(db)
        timeout_seconds = config.timeout_seconds
        max_concurrency = config.max_concurrency
        top_sites_count = config.top_sites_count
        proxy_url = config.proxy_url
        search = await create_search_run(db, username, tags=tags)
        search_id = search.id

    _active_scans[search_id] = asyncio.current_task()

    site_dict = get_site_dict(top_sites_count, tags=tags, excluded_tags=excluded_tags)
    notify = StreamingQueryNotify(queue, total_sites=len(site_dict))
    queue.put_nowait({
        "type": "started",
        "search_id": search_id,
        "username": username,
        "total_sites": len(site_dict),
    })

    # Maigret mutates this dict in place as each site check completes, so the
    # sites checked before a mid-scan cancellation remain visible here even
    # though `run_maigret_checks` itself never returns in that case.
    partial_results: dict = {}

    try:
        try:
            results = await run_maigret_checks(
                username=username,
                site_dict=site_dict,
                logger=logger,
                query_notify=notify,
                timeout=timeout_seconds,
                max_connections=max_concurrency,
                proxy=proxy_url,
                no_progressbar=True,
                output_container=partial_results,
            )
        except asyncio.CancelledError:
            found_sites = _extract_found_sites(partial_results)
            async with managed_session() as db:
                await cancel_search_run(
                    db, search_id, total_sites_checked=len(partial_results), found_sites=found_sites
                )
            if partial_results:
                save_scan_results(search_id, partial_results)
            queue.put_nowait({
                "type": "cancelled",
                "search_id": search_id,
                "total_sites_checked": len(partial_results),
                "found_count": len(found_sites),
            })
            queue.put_nowait(None)
            raise
        except Exception as exc:
            logger.error("Username search failed for '%s': %s", username, exc, exc_info=True)
            async with managed_session() as db:
                await fail_search_run(db, search_id, str(exc))
            queue.put_nowait({"type": "failed", "search_id": search_id, "error": str(exc)})
            queue.put_nowait(None)
            return

        found_sites = _extract_found_sites(results)

        async with managed_session() as db:
            await complete_search_run(db, search_id, total_sites_checked=len(site_dict), found_sites=found_sites)
        save_scan_results(search_id, results)

        queue.put_nowait({
            "type": "completed",
            "search_id": search_id,
            "total_sites_checked": len(site_dict),
            "found_count": len(found_sites),
        })
        queue.put_nowait(None)
    finally:
        _active_scans.pop(search_id, None)
