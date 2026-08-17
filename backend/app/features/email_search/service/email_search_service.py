import asyncio
import logging

import psutil
from mailcat import simple_session, via_proxy, via_tor

from app.core.database import managed_session
from app.core.scans.cancellable import TaskCancellable
from app.core.scans.run import ScanCancelled, ScanEvent, ScanOutcome, ScanRun
from app.core.scans.sse import queue_sink
from app.core.settings.email_search.crud.email_search_settings_crud import get_email_search_config
from app.features.email_search.config.mailcat_config import get_active_checkers
from app.features.email_search.crud.email_search_crud import SCAN_COLUMNS, add_provider_results
from app.features.email_search.models.email_search_models import MailSearch

logger = logging.getLogger(__name__)

FEATURE_NAME = "email_search"


async def cancel_scan(search_id: int) -> bool:
    """Request cancellation of a currently-running scan. Returns False if
    no scan with that id is currently running (already finished, or never existed)."""
    return await ScanRun.cancel(FEATURE_NAME, search_id)


_CHROMIUM_PROCESS_NAMES = {"chrome", "chromium", "headless_shell", "chrome-headless-shell"}


def _kill_orphaned_chromium(before_pids: set[int]) -> None:
    """Best-effort safety net for the pyppeteer-driven checkers (fastmail/intpl/onet).

    mailcat closes its own browser handle in a `finally` block that runs even on
    checker cancellation, but that's a cooperative asyncio-level close - if the
    Chromium process itself is wedged and never responds, cancelling our side
    doesn't reap the OS process. Diff the checker's child processes before/after
    and kill anything Chromium-shaped left behind.
    """
    try:
        for child in psutil.Process().children(recursive=True):
            if child.pid in before_pids:
                continue
            try:
                if child.name().lower() in _CHROMIUM_PROCESS_NAMES:
                    child.kill()
                    logger.warning(
                        "Killed orphaned Chromium process (pid=%s) after checker timeout", child.pid
                    )
            except psutil.NoSuchProcess:
                pass
    except psutil.Error:
        logger.debug("Chromium orphan cleanup failed", exc_info=True)


def _normalize_emails(value) -> list[str]:
    if isinstance(value, str):
        return [value]
    return list(value)


async def _run_checker(
    checker, username: str, req_session_fun, timeout: int, semaphore: asyncio.Semaphore
) -> dict:
    """Run a single mailcat checker, bounded by the concurrency semaphore.

    mailcat checkers either return a plain result dict, or a (result, error)
    tuple for the SMTP-based ones (gmail/yandex/mailDe) - same contract mailcat's
    own `print_results` handles in `src/mailcat/__init__.py`.
    """
    checker_name = checker.__name__
    async with semaphore:
        try:
            before_pids = {c.pid for c in psutil.Process().children(recursive=True)}
        except psutil.Error:
            before_pids = set()

        try:
            res = await asyncio.wait_for(
                checker(username, req_session_fun, timeout), timeout=timeout + 0.5
            )
        except Exception as exc:
            logger.debug("Checker %s failed for '%s': %s", checker_name, username, exc)
            return {"checker_name": checker_name, "found": False, "error": str(exc)}
        finally:
            _kill_orphaned_chromium(before_pids)

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
    on_event = queue_sink(queue)

    async with managed_session() as db:
        config = await get_email_search_config(db)
        timeout_seconds = config.timeout_seconds
        max_concurrency = config.max_concurrency
        proxy_url = config.proxy_url
        use_tor = config.use_tor
        enable_smtp_checks = config.enable_smtp_checks
        enable_headless_checks = config.enable_headless_checks

    checkers = get_active_checkers(enable_smtp_checks, enable_headless_checks)
    if proxy_url:
        req_session_fun = via_proxy(proxy_url)
    elif use_tor:
        req_session_fun = via_tor
    else:
        req_session_fun = simple_session

    semaphore = asyncio.Semaphore(max_concurrency)

    async def run_work(search_id: int) -> ScanOutcome:
        checked = 0
        found_providers: list[dict] = []
        tasks = [
            asyncio.ensure_future(
                _run_checker(checker, username, req_session_fun, timeout_seconds, semaphore)
            )
            for checker in checkers
        ]
        try:
            for task in asyncio.as_completed(tasks):
                result = await task
                checked += 1
                if result["found"]:
                    found_providers.append(
                        {
                            "provider_name": result["provider_name"],
                            "emails": result["emails"],
                        }
                    )
                on_event(
                    ScanEvent(
                        "progress",
                        {
                            "checked": checked,
                            "total_providers": len(checkers),
                            "checker_name": result["checker_name"],
                            "found": result["found"],
                            **(
                                {
                                    "provider_name": result["provider_name"],
                                    "emails": result["emails"],
                                }
                                if result["found"]
                                else {}
                            ),
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
    await ScanRun.execute(
        FEATURE_NAME,
        MailSearch,
        run_work,
        on_event,
        columns=SCAN_COLUMNS,
        create_fields={"username": username},
        started_fields={"username": username, "total_providers": len(checkers)},
        cancellable=cancellable,
    )
