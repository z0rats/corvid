"""Client for rmsp.nalog.ru - the ФНС Единый реестр субъектов малого и среднего
предпринимательства (МСП).

Fixed host, only the ИНН is user-supplied - never the host - so this intentionally does NOT
go through app.core.security.ssrf_guard.safe_get (see
backend/tests/core/test_ssrf_guard_coverage.py's ALLOWLISTED_FIXED_HOST_FILES).

**Verified against live captures - 2026-09-28, via this environment's own network access.**
Keyless: `GET /search-proc.json?query=<ИНН>` -> `{"data": [row...], "rowCount": N, ...}`.
Each row: `inn`, `category`, `is_active`, `nptype` (`UL`/`IP`), `isnew`, `dtregistry`
(`DD.MM.YYYY HH:MM:SS`), optional `dtregistryout`, `name_ex`, `okved1`. The meaning of the
coded fields is taken from the site's own page script (`RSMP_CATEGORY`, `search.js`):
`category` 0 "не является субъектом МСП" / 1 микро / 2 малое / 3 среднее; `is_active` false
= struck from the register (`dtregistryout`); `isnew` = "вновь созданный". `data: []` is the
normal answer for any entity that isn't a МСП (every large company).

This is a *fact* panel, not a risk source: no flag is derived from МСП status.
"""

import json
import logging

import httpx

from app.features.ru_business_check.service.source_contract import (
    require_fields,
    require_list_field,
)

logger = logging.getLogger(__name__)

RMSP_BASE_URL = "https://rmsp.nalog.ru"
REQUEST_TIMEOUT_SECONDS = 20.0
SOURCE_LABEL = "Реестр МСП"
USER_AGENT = "Corvid-OSINT (self-hosted analyst tool)"

CATEGORY_LABELS = {
    0: "Не является субъектом МСП",
    1: "Микропредприятие",
    2: "Малое предприятие",
    3: "Среднее предприятие",
}


class MspError(ValueError):
    """The service itself failed/timed out, or its answer was unreadable"""


def _date_part(value: object) -> str | None:
    """`DD.MM.YYYY HH:MM:SS` -> `DD.MM.YYYY`; anything else is dropped rather than shown."""
    if isinstance(value, str) and len(value) >= 10 and value[2] == "." and value[5] == ".":
        return value[:10]
    return None


def parse_msp(response: object, inn: str) -> dict:
    """Pure function: the search response -> the panel's result. Raises `MspError` on drift."""
    rows = require_list_field(response, "data", error=MspError, label=SOURCE_LABEL)
    row = None
    for candidate in rows:
        require_fields(
            candidate,
            ("inn", "category", "is_active", "nptype"),
            error=MspError,
            label=SOURCE_LABEL,
            where="строке реестра",
        )
        if candidate["inn"] == inn:
            row = candidate
            break

    result = {
        "checked": True,
        "found": row is not None,
        "category_code": None,
        "category": None,
        "is_active": None,
        "is_new": None,
        "registered_at": None,
        "removed_at": None,
    }
    if row is None:
        return result

    code = row["category"]
    if not isinstance(code, int) or isinstance(code, bool) or code not in CATEGORY_LABELS:
        raise MspError(f"{SOURCE_LABEL}: схема ответа изменилась — неизвестная категория {code!r}")
    result.update(
        category_code=code,
        category=CATEGORY_LABELS[code],
        is_active=bool(row["is_active"]),
        is_new=bool(row.get("isnew")),
        registered_at=_date_part(row.get("dtregistry")),
        removed_at=_date_part(row.get("dtregistryout")),
    )
    return result


async def fetch_msp_status(inn: str, *, is_individual: bool) -> tuple[dict, str]:
    """Look up `inn` in the МСП register and return `(result, raw_payload)`. Not being in
    the register is the expected, common answer (`found: False`), not a failure."""
    if not inn:
        return {"checked": False, "found": False}, ""

    async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT_SECONDS, follow_redirects=False) as client:
        try:
            response = await client.get(
                f"{RMSP_BASE_URL}/search-proc.json",
                params={"query": inn},
                headers={"User-Agent": USER_AGENT},
            )
        except httpx.HTTPError as exc:
            raise MspError(f"rmsp.nalog.ru недоступен: {exc}") from exc

    if response.status_code != 200:
        raise MspError(f"rmsp.nalog.ru вернул ошибку: HTTP {response.status_code}")
    try:
        data = response.json()
    except ValueError as exc:
        raise MspError("rmsp.nalog.ru вернул не-JSON (возможна антибот-страница)") from exc

    return parse_msp(data, inn), json.dumps(data, ensure_ascii=False, indent=2)
