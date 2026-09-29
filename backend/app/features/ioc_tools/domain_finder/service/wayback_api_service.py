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

from app.features.ioc_tools.domain_finder.service.provider_http import Provider, provider_get

logger = logging.getLogger(__name__)

WAYBACK = Provider(
    name="Wayback Machine", code="WAYBACK", base_url="https://web.archive.org/cdx/search/cdx"
)
CDX_LIMIT = 200


async def fetch_wayback_snapshots(domain: str, path: str | None = None) -> list[dict[str, Any]]:
    """Raw CDX capture rows for a domain (or, with `path`, a single page under it) - one dict
    per capture keyed by the CDX field names (urlkey, timestamp, original, mimetype,
    statuscode, digest, length). Failures raise `AppHTTPException` (`provider_http`)."""
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

    def parse(response: httpx.Response) -> list[dict[str, Any]]:
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

    return await provider_get(WAYBACK, subject=target, params=params, parse=parse)
