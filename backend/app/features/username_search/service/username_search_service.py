import asyncio
import logging

from maigret.checking import maigret as run_maigret_checks

from app.core.database import managed_session
from app.core.scans.cancellable import TaskCancellable
from app.core.scans.run import OnEvent, ScanCancelled, ScanEvent, ScanOutcome, ScanRun
from app.core.scans.sse import queue_sink
from app.core.settings.username_search.crud.username_search_settings_crud import (
    get_username_search_config,
)
from app.features.username_search.config.maigret_config import get_site_dict
from app.features.username_search.crud.username_search_crud import SCAN_COLUMNS, add_site_results
from app.features.username_search.models.username_search_models import MaigretSearch
from app.features.username_search.service.report_service import save_scan_results

logger = logging.getLogger(__name__)

FEATURE_NAME = "username_search"


async def cancel_scan(search_id: int) -> bool:
    """Request cancellation of a currently-running scan. Returns False if
    no scan with that id is currently running (already finished, or never existed)."""
    return await ScanRun.cancel(FEATURE_NAME, search_id)


class StreamingQueryNotify:
    """Forwards Maigret's per-site progress as `progress` ScanEvents, in place of
    Maigret's own terminal-printing notifier. Consumed by the SSE route handler
    (via `on_event`) to stream live "CLI-style" progress to the client.
    """

    def __init__(self, on_event: OnEvent, total_sites: int):
        self.on_event = on_event
        self.total_sites = total_sites
        self.checked = 0

    def start(self, message=None, id_type="username"):
        # No-op: the "started" event (with search_id) is emitted by ScanRun
        # itself before this notifier is even created, so the frontend has a
        # search_id to cancel by from the very first event.
        pass

    def update(self, result, is_similar=False):
        self.checked += 1
        data = {
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
            data["url_user"] = result.site_url_user
        self.on_event(ScanEvent("progress", data))

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
        found_sites.append(
            {
                "site_name": site_name,
                "url_user": site_result.get("url_user", ""),
                "http_status": http_status if isinstance(http_status, int) else None,
            }
        )
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
    on_event = queue_sink(queue)

    async with managed_session() as db:
        config = await get_username_search_config(db)
        timeout_seconds = config.timeout_seconds
        max_concurrency = config.max_concurrency
        top_sites_count = config.top_sites_count
        proxy_url = config.proxy_url

    site_dict = get_site_dict(top_sites_count, tags=tags, excluded_tags=excluded_tags)
    notify = StreamingQueryNotify(on_event, total_sites=len(site_dict))

    async def run_work(search_id: int) -> ScanOutcome:
        # Maigret mutates this dict in place as each site check completes, so
        # the sites checked before a mid-scan cancellation remain visible here
        # even though `run_maigret_checks` itself never returns in that case.
        partial_results: dict = {}
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
            if partial_results:
                save_scan_results(search_id, partial_results)
            raise ScanCancelled(
                ScanOutcome(
                    fields={
                        "total_sites_checked": len(partial_results),
                        "found_count": len(found_sites),
                    },
                    persist_children=lambda db: add_site_results(db, search_id, found_sites),
                )
            ) from None

        found_sites = _extract_found_sites(results)
        save_scan_results(search_id, results)

        return ScanOutcome(
            fields={"total_sites_checked": len(site_dict), "found_count": len(found_sites)},
            persist_children=lambda db: add_site_results(db, search_id, found_sites),
        )

    cancellable = TaskCancellable(asyncio.current_task())
    await ScanRun.execute(
        FEATURE_NAME,
        MaigretSearch,
        run_work,
        on_event,
        columns=SCAN_COLUMNS,
        create_fields={"username": username, "tags": tags, "source": "maigret"},
        started_fields={"username": username, "total_sites": len(site_dict)},
        cancellable=cancellable,
    )
