import asyncio
import logging

from maigret.checking import maigret as run_maigret_checks

from app.core.database import managed_session
from app.core.scans.cancellable import TaskCancellable
from app.core.scans.run import OnEvent, ScanCancelled, ScanEvent, ScanOutcome
from app.core.scans.sse import queue_sink
from app.core.settings.username_search.crud.username_search_settings_crud import (
    get_username_search_config,
)
from app.features.username_search.config.maigret_config import get_site_dict
from app.features.username_search.crud.username_search_crud import (
    USERNAME_SEARCH_SCANS,
    add_site_results,
)
from app.features.username_search.service.confidence_service import (
    annotate_confidence,
    build_anchors,
)
from app.features.username_search.service.pivot_service import extract_emails
from app.features.username_search.service.report_service import save_scan_results

logger = logging.getLogger(__name__)


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


# Keys Maigret's profile parsers use for a person's display name, in `ids_data`.
_NAME_KEYS = ("fullname", "full_name", "name")
# Fields socid_extractor fills with an address the profile itself published.
_EMAIL_KEYS = ("email", "emails", "public_email", "verified_email", "business_email")
MAX_DISCOVERED_PER_SITE = 20


def _build_discovered_extra(site_result: dict, searched_username: str) -> dict | None:
    """Other identifiers Maigret parsed out of a found profile page (linked usernames/IDs, links,
    display names) - pivot material for further searches, not proof they're the same person."""
    usernames = [
        {"value": value, "type": str(id_type)}
        for value, id_type in (site_result.get("ids_usernames") or {}).items()
        if isinstance(value, str) and value.lower() != searched_username.lower()
    ][:MAX_DISCOVERED_PER_SITE]
    links = [link for link in (site_result.get("ids_links") or []) if isinstance(link, str)][
        :MAX_DISCOVERED_PER_SITE
    ]
    ids_data = getattr(site_result.get("status"), "ids_data", None) or {}
    names = [
        ids_data[key].strip()
        for key in _NAME_KEYS
        if isinstance(ids_data.get(key), str) and ids_data[key].strip()
    ]
    emails = [email for key in _EMAIL_KEYS for email in extract_emails(ids_data.get(key))][
        :MAX_DISCOVERED_PER_SITE
    ]
    extra = {
        "discovered_usernames": usernames,
        "discovered_links": links,
        "discovered_names": names,
        "discovered_emails": emails,
    }
    extra = {key: value for key, value in extra.items() if value}
    return extra or None


def _extract_found_sites(results: dict, searched_username: str = "") -> list[dict]:
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
                "extra": _build_discovered_extra(site_result, searched_username),
            }
        )
    return found_sites


def _site_statuses(results: dict) -> dict[str, str]:
    """Site name -> Maigret verdict (claimed, available, unknown, illegal) for every checked site"""
    return {
        site_name: site_result["status"].status.value.lower()
        for site_name, site_result in results.items()
        if site_result.get("status") is not None
    }


async def _annotate_against_parent(
    found_sites: list[dict], username: str, parent_search_id: int
) -> None:
    """Triage `found_sites` against the run they followed. A parent that was deleted since leaves
    nothing to compare against, so the hits stay unrated. Best effort: the rating is triage, so a
    failure here must not fail the scan or, on cancellation, lose the partial results."""
    try:
        async with managed_session() as db:
            parent = await USERNAME_SEARCH_SCANS.history.get_with_results(db, parent_search_id)
            if parent is None:
                return
            anchors = build_anchors(
                ((site.site_name, site.extra) for site in parent.site_results), parent.username
            )
        annotate_confidence(found_sites, username, anchors)
    except Exception:
        logger.exception("Could not rate hits against parent run %s", parent_search_id)


async def run_scan(
    username: str,
    queue: asyncio.Queue,
    tags: list[str] | None = None,
    excluded_tags: list[str] | None = None,
    site_names: list[str] | None = None,
    parent_search_id: int | None = None,
    pivot_source: str | None = None,
) -> None:
    """Run a Maigret username search (all top sites, or only `site_names`), persisting the
    result and streaming live progress via the given queue.

    With a `parent_search_id` the found profiles are triaged against that run's findings
    (`extra["confidence"]`, see `confidence_service`).

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

    site_dict = get_site_dict(
        top_sites_count, tags=tags, excluded_tags=excluded_tags, names=site_names
    )
    notify = StreamingQueryNotify(on_event, total_sites=len(site_dict))

    def site_status_fields(results: dict) -> dict:
        # A site check keeps every verdict (only found sites become rows), so a blocked
        # check still reads as inconclusive in history.
        return {"site_statuses": _site_statuses(results)} if site_names else {}

    async def finalize(found_sites: list[dict]) -> list[dict]:
        if parent_search_id is not None:
            await _annotate_against_parent(found_sites, username, parent_search_id)
        return found_sites

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
            # Save the report before the parent lookup awaits: a repeated cancel there
            # must not lose it.
            if partial_results:
                save_scan_results(search_id, partial_results)
            found_sites = await finalize(_extract_found_sites(partial_results, username))
            raise ScanCancelled(
                ScanOutcome(
                    fields={
                        "total_sites_checked": len(partial_results),
                        "found_count": len(found_sites),
                    },
                    db_only_fields=site_status_fields(partial_results),
                    persist_children=lambda db: add_site_results(db, search_id, found_sites),
                )
            ) from None

        save_scan_results(search_id, results)
        found_sites = await finalize(_extract_found_sites(results, username))

        return ScanOutcome(
            fields={"total_sites_checked": len(site_dict), "found_count": len(found_sites)},
            db_only_fields=site_status_fields(results),
            persist_children=lambda db: add_site_results(db, search_id, found_sites),
        )

    cancellable = TaskCancellable(asyncio.current_task())
    await USERNAME_SEARCH_SCANS.execute(
        run_work,
        on_event,
        create_fields={
            "username": username,
            "tags": tags,
            "source": "maigret",
            "parent_search_id": parent_search_id,
            "pivot_source": pivot_source,
        },
        started_fields={"username": username, "total_sites": len(site_dict)},
        cancellable=cancellable,
        # A full top-sites sweep is heavy; a check of a few named sites isn't.
        heavy=not site_names,
    )
