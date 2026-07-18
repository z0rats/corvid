"""Live "how much quota is left" checks against fixed, hardcoded provider hosts.

Only the API key itself is user-supplied (via query/header) - the host is
never user-controlled - so these calls intentionally do not go through
app.core.security.ssrf_guard.safe_get. See
backend/tests/core/test_ssrf_guard_coverage.py's ALLOWLISTED_FIXED_HOST_FILES.
"""
import logging
from typing import Any

import httpx

logger = logging.getLogger(__name__)

_TIMEOUT = httpx.Timeout(10.0)


class QuotaCheckError(Exception):
    """Raised when a provider's quota endpoint can't be reached or parsed."""


async def _get_json(url: str, *, headers: dict[str, str] | None = None, params: dict[str, Any] | None = None) -> dict[str, Any]:
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.get(url, headers=headers, params=params)
            response.raise_for_status()
            return response.json()
    except httpx.HTTPStatusError as e:
        raise QuotaCheckError(f"HTTP {e.response.status_code} from provider") from e
    except httpx.HTTPError as e:
        raise QuotaCheckError(f"Could not reach provider: {e}") from e
    except ValueError as e:
        raise QuotaCheckError(f"Could not parse provider response: {e}") from e


async def fetch_virustotal_quota(apikey: str) -> dict[str, Any]:
    data = await _get_json(
        f"https://www.virustotal.com/api/v3/users/{apikey}",
        headers={"x-apikey": apikey},
    )
    quotas = data.get("data", {}).get("attributes", {}).get("quotas", {})
    daily = quotas.get("api_requests_daily", {})
    used = daily.get("used")
    allowed = daily.get("allowed")
    if used is None or allowed is None:
        raise QuotaCheckError("Response did not contain api_requests_daily quota data")
    return {"used": used, "limit": allowed, "remaining": allowed - used, "period": "daily"}


async def fetch_shodan_quota(apikey: str) -> dict[str, Any]:
    data = await _get_json("https://api.shodan.io/api-info", params={"key": apikey})
    query_credits = data.get("query_credits")
    if query_credits is None:
        raise QuotaCheckError("Response did not contain query_credits")
    # Shodan's api-info only reports remaining credits, not a fixed plan total.
    return {"used": None, "limit": None, "remaining": query_credits, "period": "query_credits"}


async def fetch_hunterio_quota(apikey: str) -> dict[str, Any]:
    data = await _get_json("https://api.hunter.io/v2/account", params={"api_key": apikey})
    searches = data.get("data", {}).get("requests", {}).get("searches", {})
    used = searches.get("used")
    available = searches.get("available")
    if used is None or available is None:
        raise QuotaCheckError("Response did not contain requests.searches quota data")
    return {"used": used, "limit": used + available, "remaining": available, "period": "monthly"}
