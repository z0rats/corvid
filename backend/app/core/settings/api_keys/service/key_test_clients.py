"""Live "does this key work" checks against fixed, hardcoded provider hosts.

Only the keys are user-supplied - the hosts never are - so these calls intentionally do not go
through app.core.security.ssrf_guard.safe_get. See backend/tests/core/test_ssrf_guard_coverage.py's
ALLOWLISTED_FIXED_HOST_FILES.

A check spends nothing from a counted allowance: it calls an account/status/token endpoint, or a
lookup on a provider with no quota at all. A service whose every call spends credits or a
daily/monthly allowance, or whose check would act on a real account, is in KEY_TEST_EXEMPT with
the reason instead (docs/adr/0026-api-key-test-free-calls-only.md). Every keyed service is in one
of the two - pinned by tests/core/settings/api_keys/test_key_test_registry.py.

Quota fields are read leniently (a missing field is None, not a SourceDriftError): the allowance
is an extra on top of the auth verdict, and a shape change there shouldn't turn a working key into
an error. The auth verdict itself never depends on the body except where noted below.

Statuses come from the HTTP status by default (`classify`); a check overrides that only where the
provider signals a bad key some other way (NVD's 404, IPQualityScore's 200 + success=false).
"""

import logging
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from typing import Any

import httpx

from app.core.settings.api_keys.schemas.key_test_schemas import KeyQuota, KeyTestStatus

logger = logging.getLogger(__name__)

_TIMEOUT = httpx.Timeout(10.0)
_USER_AGENT = "Corvid"


@dataclass(frozen=True)
class CheckOutcome:
    status: KeyTestStatus
    http_status: int | None = None
    quota: KeyQuota | None = None


def classify(status_code: int) -> KeyTestStatus:
    if 200 <= status_code < 300:
        return KeyTestStatus.OK
    if status_code in (401, 403):
        return KeyTestStatus.REJECTED
    if status_code == 402:
        return KeyTestStatus.PLAN_REQUIRED
    if status_code == 429:
        return KeyTestStatus.RATE_LIMITED
    return KeyTestStatus.ERROR


async def _request(method: str, url: str, **kwargs: Any) -> httpx.Response:
    """Raises httpx.HTTPError for network failures; the service maps that to `unreachable`."""
    async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
        return await client.request(method, url, **kwargs)


def _json(response: httpx.Response) -> dict[str, Any]:
    try:
        body = response.json()
    except ValueError:
        return {}
    return body if isinstance(body, dict) else {}


def _int(value: Any) -> int | None:
    return value if isinstance(value, int) and not isinstance(value, bool) else None


def _outcome(response: httpx.Response, quota: KeyQuota | None = None) -> CheckOutcome:
    status = classify(response.status_code)
    return CheckOutcome(status, response.status_code, quota if status is KeyTestStatus.OK else None)


async def _get(url: str, **kwargs: Any) -> CheckOutcome:
    return _outcome(await _request("GET", url, **kwargs))


# --- account / status / token endpoints ---


async def check_alienvault(keys: dict[str, str]) -> CheckOutcome:
    return await _get(
        "https://otx.alienvault.com/api/v1/users/me",
        headers={"X-OTX-API-KEY": keys["alienvault"]},
    )


async def check_anthropic(keys: dict[str, str]) -> CheckOutcome:
    return await _get(
        "https://api.anthropic.com/v1/models",
        headers={"x-api-key": keys["anthropic"], "anthropic-version": "2023-06-01"},
    )


async def check_openai(keys: dict[str, str]) -> CheckOutcome:
    return await _get(
        "https://api.openai.com/v1/models",
        headers={"Authorization": f"Bearer {keys['openai']}"},
    )


async def check_crowdstrike(keys: dict[str, str]) -> CheckOutcome:
    return _outcome(
        await _request(
            "POST",
            "https://api.crowdstrike.com/oauth2/token",
            data={
                "client_id": keys["crowdstrike_client_id"],
                "client_secret": keys["crowdstrike_client_secret"],
            },
        )
    )


async def check_mandiant(keys: dict[str, str]) -> CheckOutcome:
    # The token endpoint takes the key pair as HTTP Basic auth only (body credentials get a 400).
    return _outcome(
        await _request(
            "POST",
            "https://api.intelligence.mandiant.com/token",
            data={"grant_type": "client_credentials"},
            auth=(keys["mandiant_key"], keys["mandiant_secret"]),
        )
    )


async def check_reddit(keys: dict[str, str]) -> CheckOutcome:
    return _outcome(
        await _request(
            "POST",
            "https://www.reddit.com/api/v1/access_token",
            data={"grant_type": "client_credentials"},
            headers={"User-Agent": "Corvid/0.1"},
            auth=(keys["reddit_client_id"], keys["reddit_client_secret"]),
        )
    )


async def check_haveibeenpwned(keys: dict[str, str]) -> CheckOutcome:
    return await _get(
        "https://haveibeenpwned.com/api/v3/subscription/status",
        headers={"hibp-api-key": keys["hibp_api_key"], "User-Agent": _USER_AGENT},
    )


async def check_steam(keys: dict[str, str]) -> CheckOutcome:
    # Lists the API methods the key may call; an invalid key gets a 403.
    return await _get(
        "https://api.steampowered.com/ISteamWebAPIUtil/GetSupportedAPIList/v1/",
        params={"key": keys["steam"]},
    )


async def check_github(keys: dict[str, str]) -> CheckOutcome:
    # /rate_limit doesn't count against the rate limit it reports.
    response = await _request(
        "GET",
        "https://api.github.com/rate_limit",
        headers={
            "Authorization": f"Bearer {keys['github_pat']}",
            "Accept": "application/vnd.github+json",
        },
    )
    core = _json(response).get("resources", {}).get("core", {})
    quota = KeyQuota(
        used=_int(core.get("used")),
        limit=_int(core.get("limit")),
        remaining=_int(core.get("remaining")),
        period="hourly",
    )
    return _outcome(response, quota)


async def check_virustotal(keys: dict[str, str]) -> CheckOutcome:
    apikey = keys["virustotal"]
    response = await _request(
        "GET", f"https://www.virustotal.com/api/v3/users/{apikey}", headers={"x-apikey": apikey}
    )
    daily = _json(response).get("data", {}).get("attributes", {}).get("quotas", {})
    daily = daily.get("api_requests_daily", {})
    used, allowed = _int(daily.get("used")), _int(daily.get("allowed"))
    remaining = allowed - used if used is not None and allowed is not None else None
    return _outcome(
        response, KeyQuota(used=used, limit=allowed, remaining=remaining, period="daily")
    )


async def check_shodan(keys: dict[str, str]) -> CheckOutcome:
    response = await _request(
        "GET", "https://api.shodan.io/api-info", params={"key": keys["shodan"]}
    )
    # Shodan reports only the credits left, not a plan total.
    credits = _int(_json(response).get("query_credits"))
    return _outcome(response, KeyQuota(remaining=credits, period="query_credits"))


async def check_hunterio(keys: dict[str, str]) -> CheckOutcome:
    response = await _request(
        "GET", "https://api.hunter.io/v2/account", params={"api_key": keys["hunterio_api_key"]}
    )
    searches = _json(response).get("data", {}).get("requests", {}).get("searches", {})
    used, available = _int(searches.get("used")), _int(searches.get("available"))
    limit = used + available if used is not None and available is not None else None
    return _outcome(
        response, KeyQuota(used=used, limit=limit, remaining=available, period="monthly")
    )


async def check_ipqualityscore(keys: dict[str, str]) -> CheckOutcome:
    # Credit-usage endpoint. A bad key is a 200 with success=false, not a 401.
    response = await _request(
        "GET", f"https://www.ipqualityscore.com/api/json/account/{keys['ipqualityscore']}"
    )
    body = _json(response)
    if response.status_code == 200 and body.get("success") is False:
        message = str(body.get("message", "")).lower()
        status = KeyTestStatus.REJECTED if "key" in message else KeyTestStatus.ERROR
        return CheckOutcome(status, response.status_code)
    quota = KeyQuota(
        used=_int(body.get("usage")), remaining=_int(body.get("credits")), period="billing_cycle"
    )
    return _outcome(response, quota)


# --- lookups on providers with no quota ---


async def check_nistnvd(keys: dict[str, str]) -> CheckOutcome:
    # NVD answers an invalid apiKey with an empty 404, even for a CVE that exists.
    response = await _request(
        "GET",
        "https://services.nvd.nist.gov/rest/json/cves/2.0",
        params={"cveId": "CVE-2021-44228"},
        headers={"apiKey": keys["nist_nvd_api_key"]},
    )
    if response.status_code == 404:
        return CheckOutcome(KeyTestStatus.REJECTED, 404)
    return _outcome(response)


# abuse.ch shares one Auth-Key across its APIs; a bad one is a 403 `unknown_auth_key`.
async def check_malwarebazaar(keys: dict[str, str]) -> CheckOutcome:
    return _outcome(
        await _request(
            "POST",
            "https://mb-api.abuse.ch/api/v1/",
            headers={"Auth-Key": keys["malwarebazaar"]},
            # SHA-256 of the empty string: never a sample, always a clean "not found".
            data={
                "query": "get_info",
                "hash": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
            },
        )
    )


async def check_threatfox(keys: dict[str, str]) -> CheckOutcome:
    return _outcome(
        await _request(
            "POST",
            "https://threatfox-api.abuse.ch/api/v1/",
            headers={"Auth-Key": keys["threatfox"]},
            json={"query": "search_ioc", "search_term": "example.com"},
        )
    )


async def check_urlhaus(keys: dict[str, str]) -> CheckOutcome:
    return _outcome(
        await _request(
            "POST",
            "https://urlhaus-api.abuse.ch/v1/host/",
            headers={"Auth-Key": keys["urlhaus"]},
            data={"host": "example.com"},
        )
    )


KeyCheck = Callable[[dict[str, str]], Awaitable[CheckOutcome]]

# Service key (services config) -> its check.
KEY_TESTS: dict[str, KeyCheck] = {
    "alienvault": check_alienvault,
    "anthropic": check_anthropic,
    "crowdstrike": check_crowdstrike,
    "github": check_github,
    "haveibeenpwned": check_haveibeenpwned,
    "hunterio": check_hunterio,
    "ipqualityscore": check_ipqualityscore,
    "malwarebazaar": check_malwarebazaar,
    "mandiant": check_mandiant,
    "nistnvd": check_nistnvd,
    "openai": check_openai,
    "reddit": check_reddit,
    "shodan": check_shodan,
    "steam": check_steam,
    "threatfox": check_threatfox,
    "urlhaus": check_urlhaus,
    "virustotal": check_virustotal,
}

_DAILY = "Every call spends one request of the key's daily allowance, so it isn't tested."

# Service key -> why it has no check. Shown to the user as-is.
KEY_TEST_EXEMPT: dict[str, str] = {
    "abuseipdb": _DAILY,
    "censys": "Every Censys call spends credits and there's no free account endpoint.",
    "checkphishai": "The only call is a scan, which spends one of the plan's scans.",
    "chronoverify": "The only endpoint verifies an uploaded image.",
    "crowdsec": _DAILY,
    "dnsdumpster": _DAILY,
    "emailrepio": _DAILY,
    "ghunt_session": "Checking a Google session acts on the account and can get it flagged.",
    "google_maps": "Google bills Maps requests.",
    "instagram_session": "Checking an Instagram session acts on the account and can get it "
    "flagged.",
    "leakix": "Every call spends the plan's lookup allowance and there's no account endpoint.",
    "maltiverse": _DAILY,
    "pulsedive": _DAILY,
    "safeBrowse": _DAILY,
    "twitter": "Every read counts against the plan's monthly read cap.",
    "youtube": "Every call spends units of the daily Data API quota.",
}
