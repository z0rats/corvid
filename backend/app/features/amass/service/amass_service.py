"""
amass integration: active DNS enumeration + ASN/netblock discovery via
owasp-amass v5 (github.com/owasp-amass/amass), a Go CLI shelled out to as a
subprocess (see docs/architecture/amass.md for the client/engine split this module
works around).

A scan is two subprocess calls: `amass enum -d <domain>` submits the domain to
the already-running engine (see `amass_engine_service.py`) and waits for it to
finish or hit our own wall-clock ceiling (amass's own `-timeout` is an idle
timeout, not a hard cap); `amass subs -d <domain> -names -ip` then reads back
everything the engine currently knows about that domain as clean `hostname IP`
text lines. The engine's asset store accumulates across every scan ever run
against it, so a repeat scan of the same domain sees the union of all past
findings, not just what changed in this run - documented on `AmassSearch.result`
and surfaced to the analyst via the frontend.
"""

import asyncio
import logging
import re
from functools import lru_cache

from app.core.scans.cancellable import ProcessCancellable
from app.core.scans.run import ScanCancelled, ScanOutcome
from app.core.scans.sse import queue_sink
from app.core.utils.cli_tool_version import get_cli_tool_version
from app.features.amass.config.amass_config import (
    BINARY_NAME,
    ENUM_IDLE_TIMEOUT_MINUTES,
    SUBS_TIMEOUT_SECONDS,
    WALL_CLOCK_TIMEOUT_SECONDS,
)
from app.features.amass.crud.amass_crud import AMASS_SCANS
from app.features.amass.schemas.amass_schemas import AmassHost
from app.features.amass.service.amass_engine_service import ensure_engine_ready

logger = logging.getLogger(__name__)

_VERSION_RE = re.compile(r"(v\d+\.\d+\.\d+)")


class AmassError(ValueError):
    """The engine isn't available, or amass exited with an error"""


@lru_cache(maxsize=1)
def get_amass_version() -> str | None:
    """Return the installed amass version, or None if it's not installed.

    Not a pip package, so there's no importlib.metadata entry or PyPI-latest-version
    check to run here - a container rebuild is the only way to pick up a newer
    pinned release (see backend/Dockerfile). amass's own `-version` output is a
    bare `vX.Y.Z` (unlike subfinder/httpx's "Current Version: vX.Y.Z"), hence the
    custom regex.
    """
    return get_cli_tool_version(BINARY_NAME, version_args=("-version",), version_regex=_VERSION_RE)


async def _run_subs(domain: str) -> list[AmassHost]:
    """Read back everything the engine currently knows about `domain` as clean
    `hostname IP` text lines - see this module's docstring for why results
    accumulate across scans rather than reflecting only the most recent run."""
    process = await asyncio.create_subprocess_exec(
        BINARY_NAME,
        "subs",
        "-d",
        domain,
        "-names",
        "-ip",
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    try:
        stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=SUBS_TIMEOUT_SECONDS)
    except TimeoutError as e:
        process.kill()
        await process.wait()
        raise AmassError("Timed out reading back amass results") from e

    if process.returncode != 0:
        error = stderr.decode(errors="replace").strip()[:1000]
        raise AmassError(f"amass subs failed: {error or f'exited with code {process.returncode}'}")

    hosts: list[AmassHost] = []
    for line in stdout.decode(errors="replace").splitlines():
        line = line.strip()
        if not line or line.lower().startswith("no names were discovered"):
            continue
        parts = line.split()
        hosts.append(AmassHost(hostname=parts[0], ip=parts[1] if len(parts) > 1 else None))
    return hosts


async def run_scan_task(*, domain: str, brute_force: bool, queue: asyncio.Queue) -> None:
    """Run one amass scan, persisting its result and streaming coarse-grained
    progress via the given queue.

    Spawned as a background task by the route handler so the request isn't held
    open for the scan's full duration (which can run up to WALL_CLOCK_TIMEOUT_SECONDS).
    amass has no per-host progress callback we can stream cleanly (enum's own
    output is a raw progress bar, not discrete events), so this only emits
    "started" and a single terminal event, same as social_analyzer/git_recon.

    The `enum` subprocess (when the engine is available) is created here, before
    `ScanRun.execute()` is called, so its `ProcessCancellable` can be registered
    up front - `ScanRun` only accepts a `cancellable` alongside `run_work`, not
    one constructed lazily inside it, since a cancel request needs it registered
    before `run_work` starts awaiting.
    """
    on_event = queue_sink(queue)
    create_fields = {"domain": domain, "brute_force": brute_force}

    if not await ensure_engine_ready():

        async def run_work_unavailable(search_id: int) -> ScanOutcome:
            raise AmassError(
                "amass engine is not available (not installed, or failed to start - "
                "check server logs)"
            )

        await AMASS_SCANS.execute(
            run_work_unavailable,
            on_event,
            create_fields=create_fields,
            started_fields=create_fields,
            expected_exceptions=(AmassError,),
        )
        return

    args = [BINARY_NAME, "enum", "-d", domain, "-timeout", str(ENUM_IDLE_TIMEOUT_MINUTES)]
    if brute_force:
        args.append("-brute")
    process = await asyncio.create_subprocess_exec(
        *args, stdout=asyncio.subprocess.DEVNULL, stderr=asyncio.subprocess.DEVNULL
    )
    cancellable = ProcessCancellable(process)

    async def run_work(search_id: int) -> ScanOutcome:
        try:
            await asyncio.wait_for(process.wait(), timeout=WALL_CLOCK_TIMEOUT_SECONDS)
        except TimeoutError:
            logger.info("amass enum for %s hit the wall-clock ceiling, stopping it", domain)
            await cancellable.cancel()

        # Read findings back regardless of how enum ended (finished, hit our
        # ceiling, or was cancelled) - whatever the engine discovered before
        # stopping is still real and worth persisting.
        hosts = await _run_subs(domain)
        logger.info("amass scan for '%s': %d host(s) known", domain, len(hosts))

        outcome = ScanOutcome(
            fields={"hosts_found": len(hosts)},
            db_only_fields={"result": {"hosts": [h.model_dump() for h in hosts]}},
        )
        if cancellable.cancelled:
            raise ScanCancelled(outcome)
        return outcome

    await AMASS_SCANS.execute(
        run_work,
        on_event,
        create_fields=create_fields,
        started_fields=create_fields,
        cancellable=cancellable,
        expected_exceptions=(AmassError,),
    )
