import asyncio
import json
import logging
from urllib.parse import urlparse

from app.core.database import managed_session
from app.core.scans.cancellable import ProcessCancellable
from app.core.scans.run import ScanCancelled, ScanOutcome, ScanRun
from app.core.scans.sse import queue_sink
from app.core.settings.username_search.crud.social_analyzer_settings_crud import get_social_analyzer_config
from app.features.username_search.config.social_analyzer_config import PROCESS_WATCHDOG_SECONDS, find_binary
from app.features.username_search.crud.username_search_crud import SCAN_COLUMNS, add_site_results
from app.features.username_search.models.username_search_models import MaigretSearch

logger = logging.getLogger(__name__)

FEATURE_NAME = "social_analyzer"


async def cancel_scan(search_id: int) -> bool:
    """Request cancellation of a currently-running social-analyzer scan by
    terminating its subprocess. Returns False if no scan with that id is
    currently running."""
    return await ScanRun.cancel(FEATURE_NAME, search_id)


def _extract_found_sites(detected: list[dict]) -> list[dict]:
    """Build the list of found-site rows to persist from social-analyzer's raw JSON output"""
    found_sites = []
    for item in detected:
        link = item.get("link", "")
        site_name = urlparse(link).netloc or link
        found_sites.append({
            "site_name": site_name,
            "url_user": link,
            "http_status": None,
            "extra": {"title": item.get("title"), "rate": item.get("rate")},
        })
    return found_sites


async def run_scan(
    username: str,
    queue: asyncio.Queue,
    top_sites_count: int | None = None,
    timeout_seconds: int | None = None,
) -> None:
    """Run a social-analyzer username search via its CLI subprocess, persisting the
    result and streaming coarse-grained progress via the given queue.

    Unlike Maigret, social-analyzer's pip package can't be imported in-process (its
    installed module directory is named with a hyphen, not a valid Python
    identifier) and its public API has no per-site progress callback - so this only
    emits "started" and a single terminal event, rather than a per-site stream.
    """
    on_event = queue_sink(queue)

    async with managed_session() as db:
        config = await get_social_analyzer_config(db)
        top = top_sites_count if top_sites_count is not None else config.top_sites_count
        timeout = timeout_seconds if timeout_seconds is not None else config.timeout_seconds

    binary = find_binary()
    if binary is None:
        async def run_work(search_id: int) -> ScanOutcome:
            raise RuntimeError("social-analyzer executable not found on PATH")

        await ScanRun.execute(
            FEATURE_NAME, MaigretSearch, run_work, on_event,
            columns=SCAN_COLUMNS,
            create_fields={"username": username, "source": "social_analyzer"},
            started_fields={"username": username, "total_sites": top},
        )
        return

    process = await asyncio.create_subprocess_exec(
        binary,
        "--username", username,
        "--top", str(top),
        "--timeout", str(timeout),
        "--output", "json",
        "--method", "find",
        "--filter", "good",
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    cancellable = ProcessCancellable(process)

    async def run_work(search_id: int) -> ScanOutcome:
        try:
            stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=PROCESS_WATCHDOG_SECONDS)
        except asyncio.TimeoutError:
            process.kill()
            await process.wait()
            raise RuntimeError(
                f"social-analyzer scan exceeded the maximum runtime of {PROCESS_WATCHDOG_SECONDS}s and was terminated"
            ) from None

        if cancellable.cancelled:
            async with managed_session() as db:
                await add_site_results(db, search_id, [])
            raise ScanCancelled(ScanOutcome(fields={"total_sites_checked": 0, "found_count": 0}))

        if process.returncode != 0:
            error = stderr.decode(errors="replace").strip()[:1000] or f"social-analyzer exited with code {process.returncode}"
            raise RuntimeError(error)

        try:
            result = json.loads(stdout.decode())
        except json.JSONDecodeError as exc:
            raise RuntimeError("Invalid response from social-analyzer") from exc

        found_sites = _extract_found_sites(result.get("detected", []))
        async with managed_session() as db:
            await add_site_results(db, search_id, found_sites)

        return ScanOutcome(fields={"total_sites_checked": top, "found_count": len(found_sites)})

    await ScanRun.execute(
        FEATURE_NAME, MaigretSearch, run_work, on_event,
        columns=SCAN_COLUMNS,
        create_fields={"username": username, "source": "social_analyzer"},
        started_fields={"username": username, "total_sites": top},
        cancellable=cancellable,
    )
