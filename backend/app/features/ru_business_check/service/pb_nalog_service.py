"""Client for pb.nalog.ru (ФНС's "Прозрачный бизнес") - the official aggregator combining
ЕГРЮЛ status, mass-registration-address detection, and a handful of undocumented internal
risk indicators for a single resolved ИНН.

Fixed host, only the ИНН is user-supplied - never the host - so this intentionally does NOT
go through app.core.security.ssrf_guard.safe_get (see
backend/tests/core/test_ssrf_guard_coverage.py's ALLOWLISTED_FIXED_HOST_FILES).

**Verified against live captures - 2026-08-13, via this environment's own network access.**
Two independent two-step async job flows, both against the same general shape - submit a job,
then poll `method=get-response` on the same endpoint until it stops returning JSON `null`:

1. **Search** (`/search-proc.json`, `mode=search-all&queryAll=<query>`) - resolves an ИНН to
   a row carrying a per-result `token`. Confirmed live for a legal entity (`ul` bucket in the
   response); the individual-entrepreneur path (`ip` bucket) is assumed symmetric by naming,
   not independently confirmed - if it turns out to differ, only `_pick_matching_row` needs
   to change.
2. **Detail** (`/company-proc.json`, `method=get-request` then `method=get-response`) - takes
   the token from step 1 and returns the full profile. Confirmed live field used here:
   `masaddress` (other entities registered at the same address - the mass-registration-
   address signal). `is_p_ruk` (a boolean the response also carries) was tried as a second
   soft flag but dropped after manual re-verification against pb.nalog.ru's own UI turned up
   nothing corresponding to it there - the field's undocumented meaning wasn't just
   unconfirmed, it didn't hold up. Several other `is_p_*` booleans exist in the response
   (`is_p_uchr`/`is_p_sschr`/`is_p_taxpay`/`is_p_taxmode`/`is_p_offense`/`is_p_arrear`/
   `is_p_form1`) and remain deliberately not turned into flags for the same reason - this
   project's policy is to never assert a risk claim it can't stand behind (same reasoning as
   РДЛ/fedsfm name-only matches always being soft, never hard).

Per project decision (`docs/adr/0006-*.md`), a CAPTCHA or rate-limit response from
pb.nalog.ru is never solved or worked around - it's surfaced as a clean, user-facing error.
The site's own JS (`v2/js/pb-search.js`) distinguishes a `pbSearchCaptcha` and a
`pbRateLimit` error key inside a non-2xx response's `ERRORS` object; a 200 response can also
carry `"captchaRequired": true` inline.
"""

import asyncio
import json
import logging

import httpx

logger = logging.getLogger(__name__)

PB_NALOG_BASE_URL = "https://pb.nalog.ru"
REQUEST_TIMEOUT_SECONDS = 20.0
POLL_INTERVAL_SECONDS = 1.5
POLL_MAX_ATTEMPTS = 10
MASS_ADDRESS_DISPLAY_LIMIT = 10


class PbNalogError(ValueError):
    """The service itself failed/timed out"""


class PbNalogCaptchaRequired(PbNalogError):
    """pb.nalog.ru is asking for a CAPTCHA solve - never bypassed, always a clean error"""


class PbNalogRateLimited(PbNalogError):
    """pb.nalog.ru's own `pbRateLimit` error - a clean, honest failure, not retried
    automatically (a caller wanting a retry can simply run the scan again later)."""


def _raise_for_error_response(response: httpx.Response) -> None:
    try:
        payload = response.json()
    except ValueError:
        payload = None
    errors = (payload or {}).get("ERRORS") if isinstance(payload, dict) else None
    if errors:
        if "pbSearchCaptcha" in errors:
            raise PbNalogCaptchaRequired("pb.nalog.ru запросил капчу — попробуйте позже")
        if "pbRateLimit" in errors:
            raise PbNalogRateLimited("pb.nalog.ru: превышен лимит запросов — попробуйте позже")
    raise PbNalogError(f"pb.nalog.ru вернул ошибку: HTTP {response.status_code}")


async def _submit(client: httpx.AsyncClient, path: str, data: dict[str, str]) -> dict:
    response = await client.post(
        f"{PB_NALOG_BASE_URL}{path}",
        data=data,
        headers={"Referer": f"{PB_NALOG_BASE_URL}/"},
    )
    if response.status_code >= 400:
        _raise_for_error_response(response)
    result = response.json()
    if result.get("captchaRequired"):
        raise PbNalogCaptchaRequired("pb.nalog.ru запросил капчу — попробуйте позже")
    return result


async def _poll_until_ready(
    client: httpx.AsyncClient, path: str, job_id: str, *, token: str | None = None
) -> dict:
    poll_data = {"id": job_id, "method": "get-response"}
    if token:
        # company-proc.json's poll step needs the *new* token issued by its own
        # get-request response (not the search-step token) - confirmed live; unlike
        # search-proc.json's poll, which needs no token at all.
        poll_data["token"] = token
    for _ in range(POLL_MAX_ATTEMPTS):
        await asyncio.sleep(POLL_INTERVAL_SECONDS)
        response = await client.post(
            f"{PB_NALOG_BASE_URL}{path}",
            data=poll_data,
            headers={"Referer": f"{PB_NALOG_BASE_URL}/"},
        )
        if response.status_code >= 400:
            _raise_for_error_response(response)
        result = response.json()
        if result is not None:
            return result
    raise PbNalogError("pb.nalog.ru не ответил за отведённое время")


def _pick_matching_row(search_result: dict, inn: str, *, is_individual: bool) -> dict | None:
    """Pure function: `queryAll` is a general search, not an exact filter - the row must be
    picked by exact ИНН match from the bucket matching the entity type, rather than assumed
    to be the only/first result."""
    bucket = search_result.get("ip" if is_individual else "ul") or {}
    for row in bucket.get("data") or []:
        if row.get("inn") == inn:
            return row
    return None


def parse_detail(detail: dict) -> dict:
    """Pure function: normalize pb.nalog.ru's raw detail payload into a stable shape. Kept
    separate from the network code so it's independently unit-testable."""
    mass_address = detail.get("masaddress") or []
    companies = [
        {"inn": row.get("massinn"), "name": row.get("massnamep") or row.get("massnamec")}
        for row in mass_address[:MASS_ADDRESS_DISPLAY_LIMIT]
    ]
    return {
        "checked": True,
        "found": True,
        "mass_address_count": len(mass_address),
        "mass_address_companies": companies,
        "profile_url": None,
    }


def _empty_result() -> dict:
    return {
        "checked": False,
        "found": False,
        "mass_address_count": 0,
        "mass_address_companies": [],
        "profile_url": None,
    }


async def fetch_pb_nalog_profile(inn: str, *, is_individual: bool) -> tuple[dict, str]:
    """Look up `inn` on pb.nalog.ru and return `(result, raw_payload)`. A resolved entity
    simply not appearing in the search (a query pb.nalog.ru itself has no record of) is a
    clean, empty-but-checked result, not an error."""
    if not inn:
        return _empty_result(), ""

    async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT_SECONDS, follow_redirects=False) as client:
        search_job = await _submit(
            client, "/search-proc.json", {"mode": "search-all", "queryAll": inn, "page": "1"}
        )
        search_result = await _poll_until_ready(client, "/search-proc.json", search_job["id"])

        row = _pick_matching_row(search_result, inn, is_individual=is_individual)
        if row is None or not row.get("token"):
            result = {**_empty_result(), "checked": True}
            return result, json.dumps(search_result, ensure_ascii=False, indent=2)

        detail_job = await _submit(
            client,
            "/company-proc.json",
            {"token": row["token"], "method": "get-request", "inn": inn},
        )
        detail = await _poll_until_ready(
            client, "/company-proc.json", detail_job["id"], token=detail_job.get("token")
        )

    result = parse_detail(detail)
    result["profile_url"] = f"{PB_NALOG_BASE_URL}/search.html#mode=search-all&queryAll={inn}"
    raw_payload = json.dumps(
        {"search": search_result, "detail": detail}, ensure_ascii=False, indent=2
    )
    return result, raw_payload
