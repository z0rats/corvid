"""
Live-host probing via projectdiscovery/httpx (github.com/projectdiscovery/httpx) - a
Go CLI shelled out to as a subprocess, NOT the Python `httpx` package already used
throughout this codebase for HTTP requests. Detects which of http/https is actually
live for a domain, along with title/server/tech-stack/favicon-hash/TLS-cert data - a
useful step after subdomain enumeration (HackerTarget/RapidDNS/subfinder panels) to
see which discovered hosts are worth an analyst's attention.

Unlike this repo's other domain_finder services, httpx does its own DNS resolution
and connects directly to the target - it never goes through `ssrf_guard.safe_get`
(there's no way to hand an external Go binary our validated-IP-pinning HTTP client).
Two independent layers close that gap: `ssrf_guard.resolve_validated_ip` is checked
before the subprocess is even spawned (fails fast, consistent error codes with the
rest of domain_finder), and `-exclude private-ips` is always passed to httpx itself,
which - via the `networkpolicy` package - denies private/loopback/link-local
(including the 169.254.169.254 cloud metadata range)/multicast/reserved ranges on
every connection it makes, including redirects and DNS-rebinding re-resolutions
that a one-time pre-check alone wouldn't catch.

The compiled binary is installed as `httpx-probe`, not `httpx` (see backend/Dockerfile):
the Python `httpx` package registers its own `httpx` console-script earlier on PATH
(/opt/venv/bin) than /usr/local/bin, so the same name would silently resolve to the
wrong tool - confirmed live by actually running this against the built image before
picking the name below, not assumed.
"""

import asyncio
import json
import logging
from functools import lru_cache

from app.core.config.settings import settings
from app.core.exceptions import AppHTTPException
from app.core.security.ssrf_guard import SSRFValidationError, resolve_validated_ip
from app.core.utils.cli_tool_version import get_cli_tool_version, is_binary_available
from app.features.ioc_tools.domain_finder.schemas.domain_schemas import (
    HostProbeRequest,
    HostProbeResponse,
    HostProbeResult,
)

logger = logging.getLogger(__name__)

BINARY_NAME = "httpx-probe"
PER_HOST_TIMEOUT_SECONDS = 10
# Hard ceiling on subprocess wall-clock time: httpx tries both http and https by
# default (each up to PER_HOST_TIMEOUT_SECONDS), plus TLS-grab/tech-detect overhead.
PROCESS_TIMEOUT_SECONDS = 45


def is_httpx_available() -> bool:
    return is_binary_available(BINARY_NAME)


@lru_cache(maxsize=1)
def get_httpx_version() -> str | None:
    """Return the installed httpx version, or None if it's not installed.

    Not a pip package, so there's no importlib.metadata entry or PyPI-latest-version
    check to run here - a container rebuild is the only way to pick up a newer
    pinned release (see backend/Dockerfile).
    """
    return get_cli_tool_version(BINARY_NAME)


async def perform_host_probe(request: HostProbeRequest) -> HostProbeResponse:
    """
    Probe a domain for a live http/https host via httpx.

    Args:
        request: Validated host probe request

    Returns:
        HostProbeResponse listing every live scheme found, with title/tech/TLS detail

    Raises:
        AppHTTPException: If the domain resolves to a non-public address, httpx isn't
            installed, times out, or exits with an error
    """
    domain = request.domain
    logger.info("Starting host probe for: %s", domain)

    try:
        resolve_validated_ip(domain, allow_private=settings.security.allow_private_network_targets)
    except SSRFValidationError as e:
        logger.warning("SSRF validation failed for host probe on %s: %s", domain, e)
        raise AppHTTPException(
            status_code=400, detail=str(e), error_code="HOST_PROBE_INVALID_HOST"
        ) from e

    if not is_httpx_available():
        raise AppHTTPException(
            status_code=503, detail="httpx is not installed", error_code="HOST_PROBE_NOT_INSTALLED"
        )

    process = await asyncio.create_subprocess_exec(
        BINARY_NAME,
        "-target",
        domain,
        "-json",
        "-silent",
        "-duc",
        "-title",
        "-tech-detect",
        "-status-code",
        "-tls-grab",
        "-favicon",
        "-follow-redirects",
        "-exclude",
        "private-ips",
        "-timeout",
        str(PER_HOST_TIMEOUT_SECONDS),
        "-retries",
        "0",
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
        logger.error("httpx timed out for domain %s", domain)
        raise AppHTTPException(
            status_code=504,
            detail="httpx probe exceeded the maximum runtime",
            error_code="HOST_PROBE_TIMEOUT",
        ) from e

    if process.returncode != 0:
        error = (
            stderr.decode(errors="replace").strip()[:1000]
            or f"httpx exited with code {process.returncode}"
        )
        logger.error("httpx failed for domain %s: %s", domain, error)
        raise AppHTTPException(
            status_code=502,
            detail=f"httpx failed: {error}",
            error_code="HOST_PROBE_EXECUTION_ERROR",
        )

    results: list[HostProbeResult] = []
    for line in stdout.decode(errors="replace").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            entry = json.loads(line)
        except json.JSONDecodeError:
            logger.debug("Skipping unparseable httpx output line: %s", line)
            continue

        url = entry.get("url")
        status_code = entry.get("status_code")
        if not url or status_code is None or entry.get("failed"):
            continue

        results.append(
            HostProbeResult(
                url=url,
                final_url=entry.get("final_url") or None,
                scheme=entry.get("scheme") or "",
                status_code=status_code,
                title=entry.get("title") or None,
                webserver=entry.get("webserver") or None,
                content_type=entry.get("content_type") or None,
                content_length=entry.get("content_length"),
                technologies=entry.get("tech") or [],
                favicon_hash=entry.get("favicon") or None,
                chain_status_codes=entry.get("chain_status_codes") or [],
                tls=entry.get("tls") or None,
            )
        )

    result = HostProbeResponse(domain=domain, reachable=bool(results), results=results)
    logger.info(
        "Host probe completed for %s - reachable: %s, results: %s",
        domain,
        result.reachable,
        len(results),
    )
    return result
