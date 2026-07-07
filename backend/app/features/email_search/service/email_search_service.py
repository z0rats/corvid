import asyncio
import logging

from mailcat import simple_session, via_proxy, via_tor

from app.core.database import managed_session
from app.core.settings.email_search.crud.email_search_settings_crud import get_email_search_config
from app.features.email_search.config.mailcat_config import get_active_checkers
from app.features.email_search.crud.email_search_crud import (
    cancel_search_run,
    complete_search_run,
    create_search_run,
    fail_search_run,
)

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


def _normalize_emails(value) -> list[str]:
    if isinstance(value, str):
        return [value]
    return list(value)


async def _run_checker(checker, username: str, req_session_fun, timeout: int, semaphore: asyncio.Semaphore) -> dict:
    """Run a single mailcat checker, bounded by the concurrency semaphore.

    mailcat checkers either return a plain result dict, or a (result, error)
    tuple for the SMTP-based ones (gmail/yandex/mailDe) - same contract mailcat's
    own `print_results` handles in `src/mailcat/__init__.py`.
    """
    checker_name = checker.__name__
    async with semaphore:
        try:
            res = await asyncio.wait_for(checker(username, req_session_fun, timeout), timeout=timeout + 0.5)
        except Exception as exc:
            logger.debug("Checker %s failed for '%s': %s", checker_name, username, exc)
            return {"checker_name": checker_name, "found": False, "error": str(exc)}

        error = None
        if isinstance(res, tuple):
            res, error = res

        if not res:
            return {"checker_name": checker_name, "found": False, "error": error}

        provider_name, emails = next(iter(res.items()))
        return {
            "checker_name": checker_name,
            "found": True,
            "provider_name": provider_name,
            "emails": _normalize_emails(emails),
            "error": error,
        }


async def run_scan(username: str, queue: asyncio.Queue) -> None:
    """Run a full mailcat email search, persisting the result and streaming
    live progress via the given queue.

    Runs independently of the SSE client's connection: spawned as a background
    task by the route handler, it keeps running and persists its result even
    if the client disconnects mid-scan. It can be cancelled from another
    request via `cancel_scan(search_id)`.
    """
    async with managed_session() as db:
        config = await get_email_search_config(db)
        timeout_seconds = config.timeout_seconds
        max_concurrency = config.max_concurrency
        proxy_url = config.proxy_url
        use_tor = config.use_tor
        enable_smtp_checks = config.enable_smtp_checks
        enable_headless_checks = config.enable_headless_checks
        search = await create_search_run(db, username)
        search_id = search.id

    _active_scans[search_id] = asyncio.current_task()

    checkers = get_active_checkers(enable_smtp_checks, enable_headless_checks)
    if proxy_url:
        req_session_fun = via_proxy(proxy_url)
    elif use_tor:
        req_session_fun = via_tor
    else:
        req_session_fun = simple_session

    queue.put_nowait({
        "type": "started",
        "search_id": search_id,
        "username": username,
        "total_providers": len(checkers),
    })

    semaphore = asyncio.Semaphore(max_concurrency)
    checked = 0
    found_providers: list[dict] = []

    try:
        tasks = [
            asyncio.ensure_future(_run_checker(checker, username, req_session_fun, timeout_seconds, semaphore))
            for checker in checkers
        ]
        try:
            for task in asyncio.as_completed(tasks):
                result = await task
                checked += 1
                if result["found"]:
                    found_providers.append({
                        "provider_name": result["provider_name"],
                        "emails": result["emails"],
                    })
                queue.put_nowait({
                    "type": "progress",
                    "checked": checked,
                    "total_providers": len(checkers),
                    "checker_name": result["checker_name"],
                    "found": result["found"],
                    **({"provider_name": result["provider_name"], "emails": result["emails"]} if result["found"] else {}),
                })
        except asyncio.CancelledError:
            for task in tasks:
                task.cancel()
            async with managed_session() as db:
                await cancel_search_run(
                    db, search_id, total_providers_checked=checked, found_providers=found_providers
                )
            queue.put_nowait({
                "type": "cancelled",
                "search_id": search_id,
                "total_providers_checked": checked,
                "found_count": len(found_providers),
            })
            queue.put_nowait(None)
            raise

        async with managed_session() as db:
            await complete_search_run(
                db, search_id, total_providers_checked=len(checkers), found_providers=found_providers
            )

        queue.put_nowait({
            "type": "completed",
            "search_id": search_id,
            "total_providers_checked": len(checkers),
            "found_count": len(found_providers),
        })
        queue.put_nowait(None)
    except Exception as exc:
        logger.error("Email search failed for '%s': %s", username, exc, exc_info=True)
        async with managed_session() as db:
            await fail_search_run(db, search_id, str(exc))
        queue.put_nowait({"type": "failed", "search_id": search_id, "error": str(exc)})
        queue.put_nowait(None)
    finally:
        _active_scans.pop(search_id, None)
