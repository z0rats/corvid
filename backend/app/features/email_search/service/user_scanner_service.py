import asyncio
import logging
import os
from pathlib import Path

from app.core.config.settings import settings
from app.core.database import managed_session
from app.core.scans.cancellable import TaskCancellable
from app.core.scans.run import ScanCancelled, ScanEvent, ScanOutcome
from app.core.scans.sse import queue_sink
from app.core.settings.email_search.crud.email_search_settings_crud import get_email_search_config
from app.features.email_search.config.user_scanner_config import (
    CONFIG_ENV_VAR,
    get_runnable_modules,
    is_available,
)
from app.features.email_search.crud.email_search_crud import (
    EMAIL_SEARCH_SCANS,
    add_provider_results,
)

logger = logging.getLogger(__name__)

# Each module carries its own HTTP timeouts (often 15s); the configured per-provider timeout is
# the floor of our outer cap, not a way to shorten theirs.
MODULE_TIMEOUT_FLOOR_SECONDS = 20

PROXY_UNSUPPORTED_MESSAGE = (
    "user-scanner can't route through the configured Tor/proxy, and running it would send the "
    "address to ~150 services from this host's own IP. Turn off Tor and the proxy under "
    "Settings > Email Search to use this source."
)
NOT_INSTALLED_MESSAGE = "user-scanner is not installed in this backend image"

STATUS_REGISTERED = "registered"
STATUS_NOT_REGISTERED = "not_registered"
STATUS_ERROR = "error"


def _configure_package() -> None:
    """Point user-scanner's settings file into the data dir (its default is inside the installed
    package, which is read-only for the app user)."""
    os.environ.setdefault(CONFIG_ENV_VAR, str(Path(settings.data_dir) / "user_scanner_config.json"))


async def _run_module(module, email: str, timeout: float, semaphore: asyncio.Semaphore) -> dict:
    """Check one module and flatten its `Result` into a plain dict."""
    from user_scanner.core import engine
    from user_scanner.core.result import Status

    name = module.__name__.split(".")[-1]
    async with semaphore:
        try:
            result = await asyncio.wait_for(engine.check(module, email), timeout=timeout)
        except Exception as exc:
            logger.debug("user-scanner module %s failed for the target: %s", name, exc)
            return {
                "checker_name": name,
                "status": STATUS_ERROR,
                "error": str(exc) or type(exc).__name__,
            }

    site_name = result.site_name or name
    if result.status == Status.TAKEN:
        return {
            "checker_name": site_name,
            "status": STATUS_REGISTERED,
            "provider_name": site_name,
            "emails": [email],
            "extra": {
                "category": result.category,
                "url": result.url or None,
                "fields": dict(result.extra),
                "links": dict(result.media),
            },
        }
    if result.status == Status.AVAILABLE:
        return {"checker_name": site_name, "status": STATUS_NOT_REGISTERED}
    return {
        "checker_name": site_name,
        "status": STATUS_ERROR,
        "error": str(result.reason) if result.reason else "unknown error",
    }


async def run_scan(email: str, queue: asyncio.Queue) -> None:
    """Run every manifest-approved user-scanner module against `email`, persisting hits and
    streaming progress like the mailcat source (same event shape, plus a tri-state `status`
    so a failed or blocked check isn't shown as "not registered")."""
    on_event = queue_sink(queue)

    async with managed_session() as db:
        config = await get_email_search_config(db)
        timeout = max(config.timeout_seconds, MODULE_TIMEOUT_FLOOR_SECONDS)
        max_concurrency = config.max_concurrency
        routed = bool(config.proxy_url or config.use_tor)

    modules = get_runnable_modules() if is_available() else []
    semaphore = asyncio.Semaphore(max_concurrency)

    async def run_work(search_id: int) -> ScanOutcome:
        if not is_available():
            raise RuntimeError(NOT_INSTALLED_MESSAGE)
        if routed:
            raise RuntimeError(PROXY_UNSUPPORTED_MESSAGE)
        _configure_package()

        checked = 0
        errors = 0
        found: list[dict] = []
        tasks = [asyncio.ensure_future(_run_module(m, email, timeout, semaphore)) for m in modules]
        try:
            for next_done in asyncio.as_completed(tasks):
                result = await next_done
                checked += 1
                errors += result["status"] == STATUS_ERROR
                hit = result["status"] == STATUS_REGISTERED
                if hit:
                    found.append(
                        {
                            "provider_name": result["provider_name"],
                            "emails": result["emails"],
                            "extra": result["extra"],
                        }
                    )
                on_event(
                    ScanEvent(
                        "progress",
                        {
                            "checked": checked,
                            "total_providers": len(modules),
                            "checker_name": result["checker_name"],
                            "found": hit,
                            "status": result["status"],
                            **(
                                {
                                    "provider_name": result["provider_name"],
                                    "emails": result["emails"],
                                    "extra": result["extra"],
                                }
                                if hit
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
                        "found_count": len(found),
                        "error_count": errors,
                    },
                    persist_children=lambda db: add_provider_results(db, search_id, found),
                )
            ) from None

        return ScanOutcome(
            fields={
                "total_providers_checked": len(modules),
                "found_count": len(found),
                "error_count": errors,
            },
            persist_children=lambda db: add_provider_results(db, search_id, found),
        )

    cancellable = TaskCancellable(asyncio.current_task())
    await EMAIL_SEARCH_SCANS.execute(
        run_work,
        on_event,
        create_fields={"username": email, "source": "user_scanner"},
        started_fields={"username": email, "total_providers": len(modules)},
        cancellable=cancellable,
    )
