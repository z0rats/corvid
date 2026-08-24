"""
Passive subdomain enumeration via HackerTarget's hostsearch API.

hackertarget.com/hostsearch needs no API key and returns every hostname it
has on file for a domain as plain `hostname,ip` CSV lines - one request, no
pagination. The free tier is rate-limited to a fixed daily quota, signalled
as a plain-text "API count exceeded" line rather than a proper HTTP error
status, so that has to be detected from the response body instead.
"""

import logging

import httpx

from app.core.exceptions import AppHTTPException

logger = logging.getLogger(__name__)

HACKERTARGET_URL = "https://api.hackertarget.com/hostsearch/"
HACKERTARGET_TIMEOUT = 20.0
DEFAULT_HEADERS: dict[str, str] = {
    "User-Agent": "Corvid-Domain-Lookup/1.0",
}


async def fetch_hackertarget_hosts(domain: str) -> list[tuple[str, str | None]]:
    """
    Fetch raw hostname/IP pairs for a domain from HackerTarget's hostsearch API.

    Args:
        domain: Domain name to search for

    Returns:
        List of (hostname, ip_address) tuples

    Raises:
        AppHTTPException: For request failures, or when the free-tier daily quota is hit
    """
    logger.debug("Fetching HackerTarget hostsearch data for domain: %s", domain)

    try:
        async with httpx.AsyncClient(
            timeout=HACKERTARGET_TIMEOUT, headers=DEFAULT_HEADERS
        ) as client:
            response = await client.get(HACKERTARGET_URL, params={"q": domain})
            response.raise_for_status()

            text = response.text.strip()
            if not text:
                logger.info("HackerTarget returned an empty response for domain: %s", domain)
                return []

            first_line = text.splitlines()[0].strip().lower()
            if "api count exceeded" in first_line:
                logger.warning("HackerTarget free-tier quota hit for domain: %s", domain)
                raise AppHTTPException(
                    status_code=429,
                    detail="HackerTarget free-tier API quota exceeded, try again later",
                    error_code="HACKERTARGET_RATE_LIMITED",
                )
            if first_line.startswith("error"):
                # No hosts on file (or an invalid query our own validator already
                # rejects) - not a failure worth surfacing, just nothing found
                logger.info("HackerTarget found no hosts for domain: %s (%s)", domain, first_line)
                return []

            hosts: list[tuple[str, str | None]] = []
            for line in text.splitlines():
                hostname, _, ip = line.partition(",")
                hostname = hostname.strip()
                if hostname:
                    hosts.append((hostname, ip.strip() or None))

            logger.info("Retrieved %s hosts from HackerTarget for domain: %s", len(hosts), domain)
            return hosts

    except AppHTTPException:
        raise
    except httpx.TimeoutException as e:
        logger.error("Timeout while fetching HackerTarget data for domain %s: %s", domain, e)
        raise AppHTTPException(
            status_code=504,
            detail="Request timeout while connecting to HackerTarget",
            error_code="HACKERTARGET_TIMEOUT",
        ) from e
    except httpx.RequestError as e:
        logger.error("Request error while fetching HackerTarget data for domain %s: %s", domain, e)
        raise AppHTTPException(
            status_code=503,
            detail=f"Failed to connect to HackerTarget: {str(e)}",
            error_code="HACKERTARGET_CONNECTION_ERROR",
        ) from e
    except httpx.HTTPStatusError as e:
        logger.error(
            "HTTP status error from HackerTarget for domain %s: Status %s",
            domain,
            e.response.status_code,
        )
        raise AppHTTPException(
            status_code=e.response.status_code,
            detail=f"HackerTarget returned error: {e.response.status_code}",
            error_code="HACKERTARGET_API_ERROR",
        ) from e
    except Exception as e:
        logger.error(
            "Unexpected error while fetching HackerTarget data for domain %s: %s",
            domain,
            e,
            exc_info=True,
        )
        raise AppHTTPException(
            status_code=500,
            detail="An unexpected error occurred while fetching HackerTarget data",
            error_code="HACKERTARGET_UNEXPECTED_ERROR",
        ) from e
