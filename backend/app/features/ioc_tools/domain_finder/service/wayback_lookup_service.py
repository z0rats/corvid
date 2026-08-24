"""
Wayback Machine capture history business logic: turns CDX's raw capture rows
into a sorted snapshot list with ready-to-open web.archive.org links, for
domain_finder's "what's archived for this domain/URL" panel.
"""

import logging
from datetime import UTC, datetime

from app.features.ioc_tools.domain_finder.schemas.domain_schemas import (
    WaybackLookupRequest,
    WaybackLookupResponse,
    WaybackSnapshot,
)
from app.features.ioc_tools.domain_finder.service.wayback_api_service import (
    fetch_wayback_snapshots,
)

logger = logging.getLogger(__name__)


async def perform_wayback_lookup(wayback_request: WaybackLookupRequest) -> WaybackLookupResponse:
    """
    Look up Wayback Machine capture history for a domain (or a specific page
    under it) via the CDX API.

    Args:
        wayback_request: Validated Wayback lookup request

    Returns:
        WaybackLookupResponse containing the capture list, oldest first

    Raises:
        AppHTTPException: When the CDX request fails
    """
    domain = wayback_request.domain
    path = wayback_request.path
    logger.info("Starting Wayback lookup for: %s%s", domain, path or "")

    raw_entries = await fetch_wayback_snapshots(domain, path)

    snapshots = [
        WaybackSnapshot(
            timestamp=entry["timestamp"],
            original_url=entry["original"],
            status_code=entry.get("statuscode") or None,
            mimetype=entry.get("mimetype") or None,
            snapshot_url=f"https://web.archive.org/web/{entry['timestamp']}/{entry['original']}",
        )
        for entry in raw_entries
    ]
    snapshots.sort(key=lambda snapshot: snapshot.timestamp)

    first_capture = _parse_cdx_timestamp(snapshots[0].timestamp) if snapshots else None
    last_capture = _parse_cdx_timestamp(snapshots[-1].timestamp) if snapshots else None

    response = WaybackLookupResponse(
        domain=domain,
        total_snapshots=len(snapshots),
        first_capture=first_capture,
        last_capture=last_capture,
        snapshots=snapshots,
    )

    logger.info("Wayback lookup completed for %s - %s captures found", domain, len(snapshots))
    return response


def _parse_cdx_timestamp(timestamp: str) -> datetime | None:
    """Parse a CDX timestamp (YYYYMMDDhhmmss, always UTC) into a datetime"""
    try:
        return datetime.strptime(timestamp, "%Y%m%d%H%M%S").replace(tzinfo=UTC)
    except ValueError:
        logger.warning("Could not parse Wayback CDX timestamp: %s", timestamp)
        return None
