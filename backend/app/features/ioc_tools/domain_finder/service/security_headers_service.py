"""
Security response-header audit: fetches a domain's HTTPS response headers via
the SSRF-guarded client (`ssrf_guard.safe_get` - the target host here is the
user-supplied domain itself, unlike domain_finder's other keyless checks which
hit a fixed third-party host with the domain only as a query value) and checks
for the presence of the headers browsers/scanners commonly treat as baseline
hardening, plus a dedicated Strict-Transport-Security directive parse.
"""

import logging

import httpx

from app.core.config.settings import settings
from app.core.exceptions import AppHTTPException
from app.core.security.ssrf_guard import SSRFValidationError, safe_get
from app.features.ioc_tools.domain_finder.schemas.domain_schemas import (
    HstsInfo,
    SecurityHeadersRequest,
    SecurityHeadersResponse,
)

logger = logging.getLogger(__name__)

HEADERS_TIMEOUT = 15.0
DEFAULT_HEADERS: dict[str, str] = {"User-Agent": "Corvid-Domain-Lookup/1.0"}

# Header name (lowercase) -> analyst-facing label. This only checks
# presence/absence, not whether the value itself is well-configured (e.g. an
# overly permissive CSP still counts as "present") - that's a follow-up, not
# this MVP's job.
SECURITY_HEADERS: dict[str, str] = {
    "strict-transport-security": "Strict-Transport-Security",
    "content-security-policy": "Content-Security-Policy",
    "x-frame-options": "X-Frame-Options",
    "x-content-type-options": "X-Content-Type-Options",
    "referrer-policy": "Referrer-Policy",
    "permissions-policy": "Permissions-Policy",
    "cross-origin-opener-policy": "Cross-Origin-Opener-Policy",
    "cross-origin-resource-policy": "Cross-Origin-Resource-Policy",
    "cross-origin-embedder-policy": "Cross-Origin-Embedder-Policy",
}


async def perform_security_headers_lookup(
    request: SecurityHeadersRequest,
) -> SecurityHeadersResponse:
    """
    Fetch a domain's HTTPS response headers and audit for baseline security headers.

    Args:
        request: Validated security headers request

    Returns:
        SecurityHeadersResponse listing present/missing headers and parsed HSTS

    Raises:
        AppHTTPException: For SSRF validation failures, connection failures, or HTTP errors
    """
    domain = request.domain
    logger.info("Starting security headers check for: %s", domain)

    url = f"https://{domain}"
    try:
        async with httpx.AsyncClient(
            timeout=HEADERS_TIMEOUT, headers=DEFAULT_HEADERS, follow_redirects=False
        ) as client:
            response = await safe_get(
                client, url, allow_private=settings.security.allow_private_network_targets
            )
    except SSRFValidationError as e:
        logger.warning("SSRF validation failed for security headers check on %s: %s", domain, e)
        raise AppHTTPException(
            status_code=400, detail=str(e), error_code="SECURITY_HEADERS_INVALID_HOST"
        ) from e
    except httpx.TimeoutException as e:
        logger.error("Timeout while fetching headers for %s: %s", domain, e)
        raise AppHTTPException(
            status_code=504,
            detail="Request timeout while connecting",
            error_code="SECURITY_HEADERS_TIMEOUT",
        ) from e
    except httpx.RequestError as e:
        logger.error("Request error while fetching headers for %s: %s", domain, e)
        raise AppHTTPException(
            status_code=503,
            detail=f"Failed to connect to {domain}: {str(e)}",
            error_code="SECURITY_HEADERS_CONNECTION_ERROR",
        ) from e
    except Exception as e:
        logger.error(
            "Unexpected error fetching security headers for %s: %s", domain, e, exc_info=True
        )
        raise AppHTTPException(
            status_code=500,
            detail="An unexpected error occurred while fetching security headers",
            error_code="SECURITY_HEADERS_UNEXPECTED_ERROR",
        ) from e

    present: dict[str, str] = {}
    missing: list[str] = []
    for header_key, label in SECURITY_HEADERS.items():
        value = response.headers.get(header_key)
        if value:
            present[label] = value
        else:
            missing.append(label)

    result = SecurityHeadersResponse(
        domain=domain,
        status_code=response.status_code,
        present_headers=present,
        missing_headers=missing,
        hsts=_parse_hsts(response.headers.get("strict-transport-security")),
    )
    logger.info(
        "Security headers check completed for %s - %s present, %s missing",
        domain,
        len(present),
        len(missing),
    )
    return result


def _parse_hsts(value: str | None) -> HstsInfo | None:
    if not value:
        return None

    max_age: int | None = None
    include_subdomains = False
    preload = False
    for directive in value.split(";"):
        directive = directive.strip().lower()
        if directive.startswith("max-age="):
            try:
                max_age = int(directive.split("=", 1)[1])
            except ValueError:
                logger.debug("Could not parse HSTS max-age from: %s", directive)
        elif directive == "includesubdomains":
            include_subdomains = True
        elif directive == "preload":
            preload = True

    return HstsInfo(
        max_age=max_age, include_subdomains=include_subdomains, preload=preload, raw_value=value
    )
