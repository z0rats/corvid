"""
Passive subdomain enumeration via subfinder (github.com/projectdiscovery/subfinder),
a Go CLI shelled out to as a subprocess - its ~55 built-in scraper implementations
aren't worth reimplementing in Python, so this just drives the compiled binary
(installed at image-build time, see backend/Dockerfile) and parses its JSONL output.

No provider-config.yaml is shipped, so sources needing their own API key
(securitytrails, chaos, github, ...) silently contribute nothing rather than
erroring - subfinder auto-creates an empty one under the app user's home directory
on first run. Same posture as theHarvester's integration (see the research doc):
keyless sources only for now. `-duc` disables subfinder's own update-check network
call, which would otherwise fire against a fixed projectdiscovery.io host on every
single lookup.
"""

import asyncio
import json
import logging
from functools import lru_cache

from app.core.exceptions import AppHTTPException
from app.core.utils.cli_tool_version import get_cli_tool_version, is_binary_available
from app.features.ioc_tools.domain_finder.schemas.domain_schemas import (
    SubfinderRecord,
    SubfinderSubdomainsRequest,
    SubfinderSubdomainsResponse,
)

logger = logging.getLogger(__name__)

BINARY_NAME = "subfinder"
# Per-source timeout and overall enumeration cap passed to subfinder itself
# (its own `-timeout`/`-max-time` flags).
PER_SOURCE_TIMEOUT_SECONDS = 10
MAX_ENUMERATION_MINUTES = 1
# Hard ceiling on subprocess wall-clock time, independent of `-max-time` above -
# guards against a hung/runaway subprocess if that flag is ever dropped or a
# future subfinder version changes its behavior.
PROCESS_TIMEOUT_SECONDS = 90


def is_subfinder_available() -> bool:
    return is_binary_available(BINARY_NAME)


@lru_cache(maxsize=1)
def get_subfinder_version() -> str | None:
    """Return the installed subfinder version, or None if it's not installed.

    Not a pip package, so there's no importlib.metadata entry or PyPI-latest-version
    check to run here - a container rebuild is the only way to pick up a newer
    pinned release (see backend/Dockerfile).
    """
    return get_cli_tool_version(BINARY_NAME)


async def perform_subfinder_lookup(
    request: SubfinderSubdomainsRequest,
) -> SubfinderSubdomainsResponse:
    """
    Enumerate subdomains for a domain via subfinder's passive sources.

    Args:
        request: Validated subfinder subdomains request

    Returns:
        SubfinderSubdomainsResponse with a deduplicated subdomain list and per-source attribution

    Raises:
        AppHTTPException: If subfinder isn't installed, times out, or exits with an error
    """
    domain = request.domain
    logger.info("Starting subfinder lookup for: %s", domain)

    if not is_subfinder_available():
        raise AppHTTPException(
            status_code=503,
            detail="subfinder is not installed",
            error_code="SUBFINDER_NOT_INSTALLED",
        )

    process = await asyncio.create_subprocess_exec(
        BINARY_NAME,
        "-d",
        domain,
        "-json",
        "-silent",
        "-duc",
        "-timeout",
        str(PER_SOURCE_TIMEOUT_SECONDS),
        "-max-time",
        str(MAX_ENUMERATION_MINUTES),
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )

    try:
        stdout, stderr = await asyncio.wait_for(
            process.communicate(), timeout=PROCESS_TIMEOUT_SECONDS
        )
    except TimeoutError as e:
        process.kill()
        await process.wait()
        logger.error("subfinder timed out for domain %s", domain)
        raise AppHTTPException(
            status_code=504,
            detail="subfinder scan exceeded the maximum runtime",
            error_code="SUBFINDER_TIMEOUT",
        ) from e

    if process.returncode != 0:
        error = (
            stderr.decode(errors="replace").strip()[:1000]
            or f"subfinder exited with code {process.returncode}"
        )
        logger.error("subfinder failed for domain %s: %s", domain, error)
        raise AppHTTPException(
            status_code=502,
            detail=f"subfinder failed: {error}",
            error_code="SUBFINDER_EXECUTION_ERROR",
        )

    sources_by_host: dict[str, set[str]] = {}
    for line in stdout.decode(errors="replace").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            entry = json.loads(line)
        except json.JSONDecodeError:
            logger.debug("Skipping unparseable subfinder output line: %s", line)
            continue

        host = entry.get("host")
        if not host:
            continue
        source = entry.get("source")
        sources_by_host.setdefault(host, set())
        if source:
            sources_by_host[host].add(source)

    subdomains = sorted(sources_by_host)
    records = [
        SubfinderRecord(hostname=host, sources=sorted(sources_by_host[host])) for host in subdomains
    ]

    result = SubfinderSubdomainsResponse(
        domain=domain, subdomains=subdomains, records=records, total_records=len(records)
    )
    logger.info("subfinder lookup completed for %s - %s subdomains", domain, len(subdomains))
    return result
