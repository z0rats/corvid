"""Client for fedresurs.ru's own search backend - the Unified Federal Register of
Bankruptcy Information (ЕФРСБ), covering both legal-entity and individual bankruptcy.

Fixed host, only the ИНН is user-supplied - never the host - so this intentionally does
NOT go through app.core.security.ssrf_guard.safe_get (see
backend/tests/core/test_ssrf_guard_coverage.py's ALLOWLISTED_FIXED_HOST_FILES).

**Verified against live captures - 2026-08-13, via this environment's own network
access.** Confirmed live: `/backend/companies`/`/backend/persons` both take a
`searchString` query param (an ИНН or name) plus `limit`/`offset`, respond with
`{"pageData": [...], "found": N}`, and require a `Referer: https://fedresurs.ru/` header
(omitting it returns a bare 403 with no body). Each `pageData` row's `status` field is
free-text Russian and is itself the bankruptcy signal - confirmed against a clean entity
(ПАО СБЕРБАНК, ИНН 7707083893 -> `"Действующее"`) and two live bankrupt entities (one at
the "наблюдение" stage, one at "конкурсное производство"). `https://fedresurs.ru/company/
<guid>` is a confirmed-live (HTTP 200) deep link to a found company's own card; the
equivalent for a person (`/person/<guid>`) is assumed by API-path symmetry with
`/backend/persons`, not independently confirmed - if that assumption is wrong, only
`_profile_url` needs to change.

Per project decision (`docs/adr/0006-*.md`), a block from fedresurs.ru's anti-bot layer
(Qrator - confirmed live as an HTTP 451 on an overly broad test query) is never worked
around, only surfaced as a clean `FedresursBlocked` error - same policy as
`arbitration_service.py`'s `ArbitrationBlocked`.

`/backend/companies/{guid}/publications` (per-message bankruptcy-proceeding detail - case
numbers, dates, message types) is also confirmed live and keyless, but deliberately not
called here: the search row's own `status` field is enough for a hard/soft flag per the
methodology guide, and adding a second request per scan for detail nothing currently
consumes isn't worth the extra failure surface - a natural follow-up if richer detail is
ever wanted.
"""

import logging

import httpx

logger = logging.getLogger(__name__)

FEDRESURS_BASE_URL = "https://fedresurs.ru"
REQUEST_TIMEOUT_SECONDS = 20.0
RESULTS_LIMIT = 5


class FedresursError(ValueError):
    """The service itself failed/timed out"""


class FedresursBlocked(FedresursError):
    """fedresurs.ru's anti-bot layer (Qrator) rejected the request - confirmed live as an
    HTTP 451 on an overly broad test query. Same policy as `ArbitrationBlocked` - never
    worked around, surfaced as a clean error rather than a raw HTTP status leaking to the
    end user."""


async def _search(query: str, *, is_individual: bool) -> dict:
    path = "/backend/persons" if is_individual else "/backend/companies"
    params: dict[str, str | int] = {"limit": RESULTS_LIMIT, "offset": 0, "searchString": query}

    async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT_SECONDS, follow_redirects=False) as client:
        response = await client.get(
            f"{FEDRESURS_BASE_URL}{path}",
            params=params,
            headers={"Referer": f"{FEDRESURS_BASE_URL}/"},
        )

        if response.status_code in (403, 429, 451):
            raise FedresursBlocked(
                "fedresurs.ru временно ограничил доступ "
                "(защита от частых запросов) — попробуйте позже"
            )
        try:
            response.raise_for_status()
        except httpx.HTTPStatusError as exc:
            raise FedresursError(
                f"fedresurs.ru вернул ошибку: HTTP {exc.response.status_code}"
            ) from exc

        return response.json()


def _pick_exact_match(page_data: list[dict], inn: str) -> dict | None:
    """Pure function: `searchString` is a fuzzy/text search (confirmed live - a short
    query returned unrelated rows), so the result row must be picked by an exact ИНН
    match rather than assuming the first (or only) row is the right one."""
    return next((row for row in page_data if row.get("inn") == inn), None)


_ACTIVE_BANKRUPTCY_KEYWORDS = (
    "несостоятельн",
    "конкурсное производство",
    "наблюдение",
    "внешнее управление",
    "финансовое оздоровление",
    "реструктуризация долгов",
    "реализация имущества",
)
_RESOLVED_KEYWORDS = ("прекращ",)


def _is_active_bankruptcy(status_text: str | None) -> bool:
    """Pure function: best-effort keyword classification of fedresurs.ru's free-text
    `status` field - only 3 live-observed values back this (see module docstring), not an
    exhaustive enumeration of every status fedresurs.ru can return. Defaults to `False`
    (no flag) on anything unrecognized, same safe-default philosophy as flag_engine's own
    `_is_resolved_status` - an unclassified status should never silently read as a hard
    flag."""
    if not status_text:
        return False
    lowered = status_text.lower()
    if any(keyword in lowered for keyword in _RESOLVED_KEYWORDS):
        return False
    return any(keyword in lowered for keyword in _ACTIVE_BANKRUPTCY_KEYWORDS)


def _profile_url(guid: str | None, *, is_individual: bool) -> str | None:
    if not guid:
        return None
    kind = "person" if is_individual else "company"
    return f"{FEDRESURS_BASE_URL}/{kind}/{guid}"


async def fetch_fedresurs_status(inn: str, *, is_individual: bool) -> tuple[dict, str]:
    """Look up `inn`'s bankruptcy status and return `(result, raw_payload)`, where
    `result` is `{checked, found, status_text, is_active_bankruptcy, profile_url}`. A
    resolved entity simply not being in the bankruptcy register (`found: False`) is the
    expected, common case here, not a failure."""
    if not inn:
        return {
            "checked": False,
            "found": False,
            "status_text": None,
            "is_active_bankruptcy": False,
            "profile_url": None,
        }, ""

    data = await _search(inn, is_individual=is_individual)
    match = _pick_exact_match(data.get("pageData") or [], inn)

    result = {
        "checked": True,
        "found": match is not None,
        "status_text": match.get("status") if match else None,
        "is_active_bankruptcy": _is_active_bankruptcy(match.get("status")) if match else False,
        "profile_url": _profile_url(
            match.get("guid") if match else None, is_individual=is_individual
        ),
    }

    import json

    raw_payload = json.dumps(data, ensure_ascii=False, indent=2)
    return result, raw_payload
