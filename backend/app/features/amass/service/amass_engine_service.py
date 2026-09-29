"""Lifecycle management for the `amass engine` background process.

amass v5's `enum`/`subs` subcommands are HTTP clients to a separate collection
engine (defaults to listening on 127.0.0.1:4000) that owns the actual asset graph
- unlike subfinder/httpx, there's no single one-shot subprocess call that does the
whole job. The engine needs no flags to start and, with no database configured,
falls back to a local SQLite store under its config directory (`~/.config/amass/`,
i.e. `appuser`'s home - no Postgres/new docker-compose service needed).

Started once at app startup (`main.py`'s `handle_application_startup`, same
fire-and-forget `asyncio.create_task` shape as the favicon/blacklist background
catch-ups) and left running for the life of the process, mirroring
`telegram_bot/service/polling_service.py`'s start/stop pair - this is the second
persistent background process in this codebase, the first that's a real OS
subprocess rather than an asyncio loop. `ensure_engine_ready()` is also called
defensively before every scan, so a request still works (after a short wait) even
if startup's background task hasn't finished yet, or the engine process died
between scans and needs restarting.
"""

import asyncio
import logging

from app.core.utils.cli_tool_version import is_binary_available
from app.features.amass.config.amass_config import (
    BINARY_NAME,
    ENGINE_HOST,
    ENGINE_READY_POLL_SECONDS,
    ENGINE_READY_TIMEOUT_SECONDS,
    READY_CHECK_BINARY,
)

logger = logging.getLogger(__name__)

_engine_process: asyncio.subprocess.Process | None = None
_start_lock = asyncio.Lock()


def is_amass_available() -> bool:
    return is_binary_available(BINARY_NAME) and is_binary_available(READY_CHECK_BINARY)


async def _is_engine_ready() -> bool:
    process = await asyncio.create_subprocess_exec(
        READY_CHECK_BINARY,
        "--host",
        ENGINE_HOST,
        stdout=asyncio.subprocess.DEVNULL,
        stderr=asyncio.subprocess.DEVNULL,
    )
    return await process.wait() == 0


async def _wait_until_ready(timeout: float | None = None) -> bool:
    # `timeout` isn't just `= ENGINE_READY_TIMEOUT_SECONDS` in the signature -
    # a module-level constant used as a default value is bound once at def
    # time, so a later monkeypatch/override of the constant would silently
    # have no effect here.
    if timeout is None:
        timeout = ENGINE_READY_TIMEOUT_SECONDS
    loop = asyncio.get_event_loop()
    deadline = loop.time() + timeout
    while loop.time() < deadline:
        if await _is_engine_ready():
            return True
        await asyncio.sleep(ENGINE_READY_POLL_SECONDS)
    return False


def _engine_alive() -> bool:
    return _engine_process is not None and _engine_process.returncode is None


async def ensure_engine_ready() -> bool:
    """Start the amass engine if it isn't already running, and wait for it to
    accept connections. Idempotent and safe to call before every scan - a
    concurrent caller is held behind `_start_lock` rather than spawning a second
    engine process. Returns False (never raises) if amass isn't installed or the
    engine doesn't become ready in time, so a scan request can surface a clear
    error instead of hanging.
    """
    global _engine_process

    if not is_amass_available():
        return False

    if _engine_alive() and await _is_engine_ready():
        return True

    async with _start_lock:
        if _engine_alive() and await _is_engine_ready():
            return True

        if not _engine_alive():
            logger.info("Starting amass engine")
            _engine_process = await asyncio.create_subprocess_exec(
                BINARY_NAME,
                "engine",
                stdout=asyncio.subprocess.DEVNULL,
                stderr=asyncio.subprocess.DEVNULL,
            )
        process = _engine_process
        assert process is not None  # noqa: S101 - guaranteed by the branches above

        ready = await _wait_until_ready()
        if ready:
            logger.info("amass engine ready (pid %s)", process.pid)
        else:
            logger.error(
                "amass engine did not become ready within %ss", ENGINE_READY_TIMEOUT_SECONDS
            )
        return ready


def start_engine_in_background() -> None:
    """Fire-and-forget engine startup for app boot - doesn't block the app from
    serving other requests while the engine spins up. Failures are logged, not
    raised (same posture as `_fetch_favicons_in_background`); a scan request
    that comes in before this finishes falls back to `ensure_engine_ready()`'s
    own on-demand start."""

    async def _run() -> None:
        try:
            await ensure_engine_ready()
        except Exception:
            logger.error("Background amass engine startup failed", exc_info=True)

    asyncio.create_task(_run())


async def stop_engine() -> None:
    """Terminate the engine subprocess, if running. Safe to call even if it was
    never started."""
    global _engine_process
    if _engine_process is None:
        return
    if _engine_process.returncode is None:
        _engine_process.terminate()
        try:
            await asyncio.wait_for(_engine_process.wait(), timeout=10)
        except TimeoutError:
            _engine_process.kill()
            await _engine_process.wait()
    _engine_process = None
    logger.info("amass engine stopped")
