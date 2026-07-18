"""
RDAP (Registration Data Access Protocol) client for WHOIS-style domain lookups.

RDAP is the IETF-standardized, structured-JSON successor to plain-text WHOIS and
needs no API key. `rdap.org` (operated by APNIC Labs, endorsed by IANA as a public
bootstrap service) resolves a domain to its authoritative registry RDAP server via
an HTTP redirect, so a single fixed entrypoint covers every TLD without this app
having to maintain its own IANA bootstrap-registry mapping.
"""
import logging
from typing import Any

import httpx
from app.core.exceptions import AppHTTPException
from app.core.config.settings import settings
from app.core.security.ssrf_guard import safe_get

logger = logging.getLogger(__name__)

RDAP_BOOTSTRAP_URL = "https://rdap.org/domain/"
RDAP_TIMEOUT = 15.0
DEFAULT_HEADERS: dict[str, str] = {
    "User-Agent": "Corvid-Domain-Lookup/1.0",
    "Accept": "application/rdap+json, application/json",
}


async def fetch_rdap_domain_data(domain: str) -> tuple[dict[str, Any], str]:
    """
    Fetch RDAP registration data for a domain, following the rdap.org bootstrap redirect.

    Args:
        domain: Domain name to look up

    Returns:
        Tuple of (raw RDAP response dict, the authoritative RDAP server host that answered)

    Raises:
        AppHTTPException: For lookup failures, unsupported TLDs, or API errors
    """
    url = f"{RDAP_BOOTSTRAP_URL}{domain}"
    logger.debug("Fetching RDAP data from bootstrap: %s", url)

    try:
        async with httpx.AsyncClient(
            timeout=RDAP_TIMEOUT, headers=DEFAULT_HEADERS, follow_redirects=False
        ) as client:
            response = await safe_get(
                client, url, allow_private=settings.security.allow_private_network_targets
            )

            if response.status_code == 404:
                raise AppHTTPException(
                    status_code=404,
                    detail=f"No RDAP record found for domain: {domain}",
                    error_code="RDAP_NOT_FOUND",
                )

            response.raise_for_status()
            data = response.json()
            # `safe_get` pins the connection to a validated IP and rewrites the request's
            # Host header to the real hostname, so recover the authoritative server from
            # there rather than from `response.url` (which holds the pinned IP instead).
            rdap_server = response.request.headers.get("host", "unknown")
            logger.info("RDAP lookup succeeded for %s via %s", domain, rdap_server)
            return data, rdap_server

    except AppHTTPException:
        raise
    except httpx.TimeoutException as e:
        logger.error("Timeout while fetching RDAP data for domain %s: %s", domain, e)
        raise AppHTTPException(
            status_code=504,
            detail="Request timeout while connecting to RDAP service",
            error_code="RDAP_TIMEOUT",
        )
    except httpx.RequestError as e:
        logger.error("Request error while fetching RDAP data for domain %s: %s", domain, e)
        raise AppHTTPException(
            status_code=503,
            detail=f"Failed to connect to RDAP service: {str(e)}",
            error_code="RDAP_CONNECTION_ERROR",
        )
    except httpx.HTTPStatusError as e:
        logger.error("HTTP status error from RDAP for domain %s: Status %s", domain, e.response.status_code)
        raise AppHTTPException(
            status_code=e.response.status_code,
            detail=f"RDAP service returned error: {e.response.status_code}",
            error_code="RDAP_API_ERROR",
        )
    except Exception as e:
        logger.error("Unexpected error while fetching RDAP data for domain %s: %s", domain, e, exc_info=True)
        raise AppHTTPException(
            status_code=500,
            detail="An unexpected error occurred while fetching RDAP data",
            error_code="RDAP_UNEXPECTED_ERROR",
        )
