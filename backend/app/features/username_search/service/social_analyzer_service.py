import asyncio
import json
import logging
from urllib.parse import urlparse

from app.core.database import managed_session
from app.core.settings.username_search.crud.social_analyzer_settings_crud import get_social_analyzer_config
from app.features.username_search.config.social_analyzer_config import PROCESS_WATCHDOG_SECONDS, find_binary
from app.features.username_search.crud.username_search_crud import (
    cancel_search_run,
    complete_search_run,
    create_search_run,
    fail_search_run,
)

logger = logging.getLogger(__name__)

# Process handles for currently-running social-analyzer scans, keyed by search_id,
# so a separate request can reach back in and cancel one (see username_search_service's
# equivalent registry - kept separate since these are subprocesses, not asyncio tasks).
_active_processes: dict[int, asyncio.subprocess.Process] = {}

# search_ids killed via cancel_scan(), so run_scan can tell "the user cancelled
# this" apart from "the subprocess crashed with a nonzero/negative exit code" -
# process.communicate() returns normally either way, it doesn't raise
# CancelledError just because the OS process was killed by another request.
_cancelled_search_ids: set[int] = set()


def cancel_scan(search_id: int) -> bool:
    """Request cancellation of a currently-running social-analyzer scan by killing
    its subprocess. Returns False if no scan with that id is currently running."""
    process = _active_processes.get(search_id)
    if process is None or process.returncode is not None:
        return False
    _cancelled_search_ids.add(search_id)
    process.kill()
    return True


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
    async with managed_session() as db:
        config = await get_social_analyzer_config(db)
        top = top_sites_count if top_sites_count is not None else config.top_sites_count
        timeout = timeout_seconds if timeout_seconds is not None else config.timeout_seconds
        search = await create_search_run(db, username, source="social_analyzer")
        search_id = search.id

    queue.put_nowait({
        "type": "started",
        "search_id": search_id,
        "username": username,
        "total_sites": top,
    })

    binary = find_binary()
    if binary is None:
        error = "social-analyzer executable not found on PATH"
        logger.error(error)
        async with managed_session() as db:
            await fail_search_run(db, search_id, error)
        queue.put_nowait({"type": "failed", "search_id": search_id, "error": error})
        queue.put_nowait(None)
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
    _active_processes[search_id] = process

    try:
        try:
            stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=PROCESS_WATCHDOG_SECONDS)
        except asyncio.CancelledError:
            process.kill()
            await process.wait()
            async with managed_session() as db:
                await cancel_search_run(db, search_id, total_sites_checked=0, found_sites=[])
            queue.put_nowait({
                "type": "cancelled", "search_id": search_id, "total_sites_checked": 0, "found_count": 0,
            })
            queue.put_nowait(None)
            raise
        except asyncio.TimeoutError:
            process.kill()
            await process.wait()
            error = f"social-analyzer scan exceeded the maximum runtime of {PROCESS_WATCHDOG_SECONDS}s and was terminated"
            logger.error("%s ('%s')", error, username)
            async with managed_session() as db:
                await fail_search_run(db, search_id, error)
            queue.put_nowait({"type": "failed", "search_id": search_id, "error": error})
            queue.put_nowait(None)
            return

        if search_id in _cancelled_search_ids:
            async with managed_session() as db:
                await cancel_search_run(db, search_id, total_sites_checked=0, found_sites=[])
            queue.put_nowait({
                "type": "cancelled", "search_id": search_id, "total_sites_checked": 0, "found_count": 0,
            })
            queue.put_nowait(None)
            return

        if process.returncode != 0:
            error = stderr.decode(errors="replace").strip()[:1000] or f"social-analyzer exited with code {process.returncode}"
            logger.error("social-analyzer scan failed for '%s': %s", username, error)
            async with managed_session() as db:
                await fail_search_run(db, search_id, error)
            queue.put_nowait({"type": "failed", "search_id": search_id, "error": error})
            queue.put_nowait(None)
            return

        try:
            result = json.loads(stdout.decode())
        except json.JSONDecodeError as exc:
            error = "Invalid response from social-analyzer"
            logger.error("%s for '%s': %s", error, username, exc)
            async with managed_session() as db:
                await fail_search_run(db, search_id, error)
            queue.put_nowait({"type": "failed", "search_id": search_id, "error": error})
            queue.put_nowait(None)
            return

        found_sites = _extract_found_sites(result.get("detected", []))

        async with managed_session() as db:
            await complete_search_run(db, search_id, total_sites_checked=top, found_sites=found_sites)

        queue.put_nowait({
            "type": "completed",
            "search_id": search_id,
            "total_sites_checked": top,
            "found_count": len(found_sites),
        })
        queue.put_nowait(None)
    finally:
        _active_processes.pop(search_id, None)
        _cancelled_search_ids.discard(search_id)
