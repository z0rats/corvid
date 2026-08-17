"""Client for kad.arbitr.ru's case search - "Картотека арбитражных дел" (arbitration case
registry). Per the ТЗ this counts as an official source (with an API third-party services
already build on), unlike ЕГРЮЛ/РДЛ where scraping vs. a paid reseller was a real decision
(see `docs/adr/0006-*.md`).

Fixed host, only the searched ИНН is user-supplied - never the host - so this intentionally
does NOT go through app.core.security.ssrf_guard.safe_get (see
backend/tests/core/test_ssrf_guard_coverage.py's ALLOWLISTED_FIXED_HOST_FILES).

**Unverified against a live capture** (same caveat as egrul_service.py/
disqualified_persons_service.py): the request/response shape below follows kad.arbitr.ru's
publicly known search flow (the same JSON endpoint its own front-end calls, reverse-engineered
by several existing open-source kad.arbitr.ru clients) rather than a live-tested capture -
this repo's sandbox has no way to browse the live site during development. If a live capture
shows different field names, only `_search` and `_parse_response` need to change.

Per project decision (same as the other two Stage 1/2 sources), a CAPTCHA challenge from
kad.arbitr.ru is never solved or worked around - it's surfaced as a clean, user-facing
`ArbitrationError`.

Known limitation: the search-result JSON often doesn't carry a case's claim amount (it lives
on the case's own card page, `https://kad.arbitr.ru/Card/<CaseId>`, a page-per-case fetch this
module doesn't make to avoid one extra request per case found) - `claim_amount` is left `None`
whenever the search response doesn't already include it, and flag_engine's "large claim" flag
degrades gracefully to relying on case *count* alone in that case.
"""

import logging

import httpx

logger = logging.getLogger(__name__)

KAD_ARBITR_BASE_URL = "https://kad.arbitr.ru"
REQUEST_TIMEOUT_SECONDS = 20.0
CASES_PER_PAGE = 25


class ArbitrationError(ValueError):
    """The service itself failed/timed out"""


class ArbitrationCaptchaRequired(ArbitrationError):
    """kad.arbitr.ru is asking for a CAPTCHA solve - never bypassed, always a clean error"""


class ArbitrationBlocked(ArbitrationError):
    """kad.arbitr.ru's anti-bot layer (DDoS-Guard) rejected the request - confirmed live
    as an HTTP 451 with a 'Доступ к сервису ограничен... большим количеством запросов'
    HTML page, not a CAPTCHA prompt. Same policy as `ArbitrationCaptchaRequired` - never
    worked around, surfaced as a clean error rather than a raw HTTP status leaking to the
    end user."""


async def _search(inn: str) -> dict:
    payload = {
        "Sides": [{"Name": inn, "Type": None}],
        "DateFrom": None,
        "DateTo": None,
        "CaseNumbers": [],
        "WithVKSInstances": False,
        "Courts": [],
        "Judges": [],
        "CaseTypes": [],
        "Page": 1,
        "Count": CASES_PER_PAGE,
    }
    async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT_SECONDS, follow_redirects=False) as client:
        response = await client.post(f"{KAD_ARBITR_BASE_URL}/Kad/SearchInstances", json=payload)

        if (
            response.status_code in (403, 429, 451)
            or "ddos-guard" in response.headers.get("server", "").lower()
        ):
            raise ArbitrationBlocked(
                "kad.arbitr.ru временно ограничил доступ (защита от частых запросов) — "
                "попробуйте позже"
            )
        try:
            response.raise_for_status()
        except httpx.HTTPStatusError as exc:
            raise ArbitrationError(
                f"kad.arbitr.ru вернул ошибку: HTTP {exc.response.status_code}"
            ) from exc
        data = response.json()

    if data.get("CaptchaRequired") or data.get("Captcha"):
        raise ArbitrationCaptchaRequired(
            "kad.arbitr.ru запросил капчу — автоматическая проверка недоступна, попробуйте позже"
        )
    if data.get("Success") is False:
        raise ArbitrationError(f"kad.arbitr.ru вернул ошибку: {data}")

    return data


_ROLE_MAP = {
    "истец": "plaintiff",
    "ответчик": "defendant",
    "заявитель": "plaintiff",
    "заинтересованное лицо": "other",
    "третье лицо": "other",
}


def _coerce_amount(value) -> float | None:
    """kad.arbitr.ru's own JSON isn't guaranteed to send claim amounts as a clean
    number (a live capture may show a formatted string) - coerce defensively rather
    than let an unexpected type blow up the whole scan over one field."""
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    try:
        return float(str(value).replace(" ", "").replace(",", "."))
    except ValueError:
        return None


def _classify_role(side_role: str | None, inn: str) -> str:
    """Map kad.arbitr.ru's free-text side role (Russian) to a stable code. Falls back to
    'other' for anything not recognized rather than guessing - an unrecognized role should
    never silently count as 'defendant' for flag purposes."""
    if not side_role:
        return "other"
    return _ROLE_MAP.get(side_role.strip().lower(), "other")


def parse_response(data: dict, inn: str) -> list[dict]:
    """Pure function: extract a normalized case list from kad.arbitr.ru's search-response
    JSON. Kept separate from the network code above so it's independently unit-testable."""
    items = (data.get("Result") or {}).get("Items") or []
    cases: list[dict] = []

    for item in items:
        case_id = item.get("CaseId") or item.get("Id")
        case_number = item.get("CaseNumber") or item.get("Number")
        if not case_number:
            continue

        sides = item.get("Sides") or []
        # The searched ИНН can appear as either side - determine our own role from
        # whichever side entry's Inn matches the query, not just "the first side".
        own_side = next(
            (s for s in sides if str(s.get("Inn") or "") == inn), sides[0] if sides else {}
        )
        role = _classify_role(own_side.get("Role"), inn)

        cases.append(
            {
                "case_number": case_number,
                "date_registered": item.get("DateRegister") or item.get("Date"),
                "role": role,
                "status": item.get("Status") or item.get("CaseStatus"),
                "court": item.get("Court") or item.get("CourtName"),
                "claim_amount": _coerce_amount(item.get("Sum") or item.get("ClaimAmount")),
                "case_url": f"{KAD_ARBITR_BASE_URL}/Card/{case_id}" if case_id else None,
            }
        )

    return cases


async def fetch_arbitration_cases(inn: str) -> tuple[list[dict], str]:
    """Look up arbitration cases for `inn` and return `(cases, raw_payload)`. Returns an
    empty list (not an error) when the entity simply has no cases - a clean history is the
    expected, common case here, not a failure."""
    if not inn:
        return [], ""

    data = await _search(inn)
    cases = parse_response(data, inn)

    import json

    raw_payload = json.dumps(data, ensure_ascii=False, indent=2)
    return cases, raw_payload
