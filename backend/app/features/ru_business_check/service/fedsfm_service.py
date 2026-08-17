"""Client for fedsfm.ru's own TerroristSearch endpoint - Росфинмониторинга's public
Перечень организаций и физических лиц, причастных к терроризму/финансированию
распространения оружия массового уничтожения.

Fixed host, only the searched full name is user-supplied - never the host - so this
intentionally does NOT go through app.core.security.ssrf_guard.safe_get (see
backend/tests/core/test_ssrf_guard_coverage.py's ALLOWLISTED_FIXED_HOST_FILES).

**Verified against live captures - 2026-08-13, via this environment's own network
access.** Confirmed live:
```
POST https://fedsfm.ru/TerroristSearch
Content-Type: application/json
Body: {"rowIndex": 0, "pageLength": 10, "searchText": "<query>"}
-> {"IsError": false, "recordsTotal": N, "recordsFiltered": N,
   "data": [{"Id", "TerroristTypeName", "FullName", "StatusName"}, ...]}
```
Keyless, no CAPTCHA, no token - but the site's own WAF rejects any request with no
`User-Agent` header at all with a bare HTTP 403 (confirmed live; a `Referer` header alone
does not help, a browser-shaped `User-Agent` alone does).

`searchText` does a substring match against the full `FullName` string (which itself
embeds a record number, DOB, and birthplace as free text - e.g. "10198. КОСЯКОВ ДМИТРИЙ
ЕВГЕНЬЕВИЧ, 06.06.1989 г.р. , Г. ИВАНОВО;"), so a common surname returns many loosely-
related hits - same false-positive shape as disqualified_persons_service.py, and the same
project policy applies: a name-only match here is NEVER a confirmed hard flag, always
`requires_manual_review` - see check_terrorist_list's docstring.

**TLS**: fedsfm.ru serves a certificate chained to the Russian national root CA ("Russian
Trusted Root/Sub CA", Минцифры ГУЦ), which isn't present in a standard trust store
(`SSL certificate problem: unable to get local issuer certificate`, confirmed live). This
client scopes `verify=False` to only itself rather than bundling that CA into the
container's trust store system-wide - see docs/adr/0007-*.md for why.
"""

import json
import logging

import httpx

logger = logging.getLogger(__name__)

FEDSFM_SEARCH_URL = "https://fedsfm.ru/TerroristSearch"
REQUEST_TIMEOUT_SECONDS = 20.0
# No pagination concerns for a due-diligence use case (checking one name, not enumerating
# the full list) - a generous single page is plenty, same reasoning as the Phase 2 plan.
RESULTS_PAGE_LENGTH = 10

# A browser-shaped User-Agent is required - fedsfm.ru's WAF 403s any request without one
# (confirmed live). Not spoofing anything beyond this one header.
_USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
)


class FedsfmError(ValueError):
    """The service itself failed/timed out, or returned something that couldn't be
    parsed as the expected JSON shape (e.g. a WAF block page)."""


async def _search(full_name: str) -> dict:
    body = {"rowIndex": 0, "pageLength": RESULTS_PAGE_LENGTH, "searchText": full_name}

    async with httpx.AsyncClient(
        timeout=REQUEST_TIMEOUT_SECONDS, follow_redirects=False, verify=False
    ) as client:
        try:
            response = await client.post(
                FEDSFM_SEARCH_URL, json=body, headers={"User-Agent": _USER_AGENT}
            )
            response.raise_for_status()
        except httpx.HTTPStatusError as exc:
            raise FedsfmError(f"fedsfm.ru вернул ошибку: HTTP {exc.response.status_code}") from exc
        except httpx.HTTPError as exc:
            raise FedsfmError(f"fedsfm.ru недоступен: {exc}") from exc

        try:
            data = response.json()
        except ValueError as exc:
            raise FedsfmError("fedsfm.ru вернул неожиданный (не JSON) ответ") from exc

    if data.get("IsError"):
        raise FedsfmError("fedsfm.ru сообщил об ошибке поиска")

    return data


def _parse_matches(data: dict) -> list[dict]:
    """Pure function: extract match rows from the search response, kept separate from
    the network code above so it's independently unit-testable."""
    matches: list[dict] = []
    for row in data.get("data") or []:
        full_name = row.get("FullName")
        if not full_name:
            continue
        matches.append(
            {
                "id": row.get("Id"),
                "full_name": full_name,
                "terrorist_type": row.get("TerroristTypeName"),
                "status": row.get("StatusName"),
            }
        )
    return matches


async def check_terrorist_list(full_name: str) -> tuple[dict, str]:
    """Search fedsfm.ru's terrorism/WMD-financing list for `full_name` and return
    `(result, raw_payload)`, where `result` is `{checked, matched, requires_manual_review,
    matches}` and `raw_payload` is the verbatim search-response JSON.

    Per project decision, a match is NEVER auto-confirmed as a hard flag - the list gives
    no disambiguating identifier beyond full name (same reasoning as
    disqualified_persons_service.py), so every match is surfaced as
    `requires_manual_review`.
    """
    if not full_name or not full_name.strip():
        return {
            "checked": False,
            "matched": False,
            "requires_manual_review": False,
            "matches": [],
        }, ""

    data = await _search(full_name.strip())
    matches = _parse_matches(data)

    result = {
        "checked": True,
        "matched": bool(matches),
        "requires_manual_review": bool(matches),
        "matches": matches,
    }
    return result, json.dumps(data, ensure_ascii=False, indent=2)
