import logging

import httpx

from app.features.username_search.schemas.username_search_schemas import (
    HudsonRockCheckResponse,
    HudsonRockStealerSummary,
)

logger = logging.getLogger(__name__)

BASE_URL = "https://cavalier.hudsonrock.com/api/json/v2/osint-tools/search-by-username"
REQUEST_TIMEOUT_SECONDS = 10.0


def _build_response(username: str, data: dict) -> HudsonRockCheckResponse:
    """Trim Hudson Rock's raw payload down to what the compact panel needs - date/computer/OS
    per infection, not the full masked-login/password lists (those stay exclusive to the
    fuller ioc_lookup provider card)."""
    stealers = [
        HudsonRockStealerSummary(
            date_compromised=s.get("date_compromised"),
            computer_name=s.get("computer_name"),
            operating_system=s.get("operating_system"),
        )
        for s in data.get("stealers", [])
    ]
    return HudsonRockCheckResponse(username=username, stealers=stealers)


async def check_username(username: str) -> HudsonRockCheckResponse:
    """Check for infostealer/malware-log exposure using Hudson Rock's free, keyless public API"""
    logger.debug("Checking username %s with Hudson Rock", username)
    async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT_SECONDS) as client:
        response = await client.get(BASE_URL, params={"username": username})
        response.raise_for_status()
        return _build_response(username, response.json())
