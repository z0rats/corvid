"""
Wayback Machine (archive.org) capture history via the CDX API.

CDX (`web.archive.org/cdx/search/cdx`) needs no API key and returns the full
list of captures for a URL/domain - timestamps, status codes, mimetypes -
unlike the Availability API (`archive.org/wayback/available`), which only
returns the single closest snapshot to a given time. `output=json` serves a
2D array (first row is the field-name header, not a JSON object per row).
"""

import logging
from typing import Any

import httpx

from app.core.exceptions import AppHTTPException

logger = logging.getLogger(__name__)

CDX_URL = "https://web.archive.org/cdx/search/cdx"
CDX_TIMEOUT = 20.0
CDX_LIMIT = 200
DEFAULT_HEADERS: dict[str, str] = {
    "User-Agent": "Corvid-Domain-Lookup/1.0",
    "Accept": "application/json",
}


async def fetch_wayback_snapshots(domain: str, path: str | None = None) -> list[dict[str, Any]]:
    """
    Fetch raw CDX capture rows for a domain (or a specific page under it) from
    the Wayback Machine.

    Args:
        domain: Domain name to search for
        path: Optional path to narrow the query to a single page rather than
            the whole domain

    Returns:
        List of dicts, one per capture, keyed by the CDX field names
        (urlkey, timestamp, original, mimetype, statuscode, digest, length)

    Raises:
        AppHTTPException: For request failures or an unparseable response
    """
    target = f"{domain}{path}" if path else domain
    params: dict[str, str | int] = {
        "url": target,
        "output": "json",
        "collapse": "timestamp:8",
        # Negative limit returns the *last* N captures rather than the first N -
        # an analyst wants recent history (what did this now-dead page look
        # like last week), not the oldest snapshot from over a decade ago
        "limit": -CDX_LIMIT,
    }
    if not path:
        # Domain-wide query: match every page under the domain, not just its
        # root. An exact-page query (path given) needs no matchType - CDX
        # already defaults to an exact match on the given URL.
        params["matchType"] = "domain"

    logger.debug("Fetching Wayback CDX data for target: %s", target)

    try:
        async with httpx.AsyncClient(timeout=CDX_TIMEOUT, headers=DEFAULT_HEADERS) as client:
            response = await client.get(CDX_URL, params=params)
            response.raise_for_status()

            if not response.content:
                logger.info("Wayback CDX returned an empty response for target: %s", target)
                return []

            rows = response.json()
            if not rows or len(rows) < 2:
                # Only the header row (or nothing) - no captures found
                logger.info("No Wayback captures found for target: %s", target)
                return []

            fields = rows[0]
            entries = [dict(zip(fields, row, strict=True)) for row in rows[1:]]
            logger.info("Retrieved %s Wayback captures for target: %s", len(entries), target)
            return entries

    except httpx.TimeoutException as e:
        logger.error("Timeout while fetching Wayback CDX data for target %s: %s", target, e)
        raise AppHTTPException(
            status_code=504,
            detail="Request timeout while connecting to the Wayback Machine",
            error_code="WAYBACK_TIMEOUT",
        ) from e
    except httpx.RequestError as e:
        logger.error("Request error while fetching Wayback CDX data for target %s: %s", target, e)
        raise AppHTTPException(
            status_code=503,
            detail=f"Failed to connect to the Wayback Machine: {str(e)}",
            error_code="WAYBACK_CONNECTION_ERROR",
        ) from e
    except httpx.HTTPStatusError as e:
        logger.error(
            "HTTP status error from Wayback CDX for target %s: Status %s",
            target,
            e.response.status_code,
        )
        raise AppHTTPException(
            status_code=e.response.status_code,
            detail=f"Wayback Machine returned error: {e.response.status_code}",
            error_code="WAYBACK_API_ERROR",
        ) from e
    except ValueError as e:
        logger.error("Could not parse Wayback CDX JSON response for target %s: %s", target, e)
        raise AppHTTPException(
            status_code=502,
            detail="Wayback Machine returned an unexpected (non-JSON) response",
            error_code="WAYBACK_INVALID_RESPONSE",
        ) from e
    except Exception as e:
        logger.error(
            "Unexpected error while fetching Wayback CDX data for target %s: %s",
            target,
            e,
            exc_info=True,
        )
        raise AppHTTPException(
            status_code=500,
            detail="An unexpected error occurred while fetching Wayback Machine data",
            error_code="WAYBACK_UNEXPECTED_ERROR",
        ) from e
