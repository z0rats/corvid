"""Client for bo.nalog.gov.ru - ГИР БО, the state register of accounting (financial)
statements filed with the ФНС.

Fixed host, only the ИНН is user-supplied - never the host - so this intentionally does NOT
go through app.core.security.ssrf_guard.safe_get (see
backend/tests/core/test_ssrf_guard_coverage.py's ALLOWLISTED_FIXED_HOST_FILES).

**Verified against live captures - 2026-09-28, via this environment's own network access.**
Keyless. The only gate found: the library-default `python-httpx/...` User-Agent is refused
with a 403; any other User-Agent passes (a `Referer` isn't required - 200 without one), so
this client sends an honest, identifying one rather than posing as a browser. Three requests
(the request flow and field meanings were first mapped by the open-source inn-check-ru
project's `fetch_counterparty.py`; every shape below was re-confirmed live):

1. `GET /advanced-search/organizations/search?query=<ИНН>&page=0` ->
   `{"content": [{id, inn, shortName, ogrn, ..., bfo: {...}}]}`. The query is a text search:
   the exact row is picked by ИНН, and **`inn` comes back HTML-wrapped**
   (`<strong>5036045205</strong>`, the match highlight) - tags must be stripped before
   comparing.
2. `GET /nbo/organizations/<id>/bfo/` -> a list of one entry per filed period:
   `{id, period, actualBfoDate, gainSum, actives, ...}`. `gainSum` is the period's revenue
   (equal to line 2110 in all 10 periods cross-checked by inn-check-ru), `actives` its balance
   total, both in **thousand rubles** (the form's own unit).
3. `GET /nbo/bfo/<bfo id>/details` -> a one-element list; `balance.current<line>` and
   `financialResult.current<line>` hold the statement lines (`previous<line>` the prior
   year's): 1200 оборотные активы, 1250 денежные средства, 1300 капитал и резервы,
   1400/1500 долго-/краткосрочные обязательства, 1600 итог баланса, 2110 выручка,
   2400 чистая прибыль.

**An empty result is normal, not a failure**: banks, insurers, individual entrepreneurs,
and entities that never published have no statements here. `found: False` /
`has_reports: False` say so, and `flag_engine` derives nothing from them.

Per project decision (`docs/adr/0006-*.md`), an anti-bot response (401/403/429/451) is never
worked around, only surfaced as `GirBoBlocked`.
"""

import asyncio
import json
import logging
import math
import re

import httpx

from app.features.ru_business_check.service.source_contract import (
    require_dict,
    require_fields,
    require_list_field,
)

logger = logging.getLogger(__name__)

GIR_BO_BASE_URL = "https://bo.nalog.gov.ru"
REQUEST_TIMEOUT_SECONDS = 20.0
PERIODS_LIMIT = 3
SOURCE_LABEL = "ГИР БО"
USER_AGENT = "Corvid-OSINT (self-hosted analyst tool)"
UNIT = "тыс. руб."

_TAG_RE = re.compile(r"<[^>]+>")

# statement line -> result field, per section of the details form
_BALANCE_LINES = {
    "current1200": "current_assets",
    "current1250": "cash",
    "current1300": "equity",
    "current1400": "long_term_liabilities",
    "current1500": "current_liabilities",
    "current1600": "assets",
}
_RESULT_LINES = {"current2110": "revenue", "current2400": "net_profit"}


class GirBoError(ValueError):
    """The service itself failed/timed out, or its answer was unreadable"""


class GirBoBlocked(GirBoError):
    """bo.nalog.gov.ru's anti-bot layer rejected the request - never worked around."""


def _strip_tags(value: object) -> str | None:
    if not isinstance(value, str):
        return None
    return _TAG_RE.sub("", value).strip()


def _number(value: object) -> float | None:
    """A finite number, or None. Statement lines are `null` when the filer left them out
    (small filers use simplified forms), which is data, not drift."""
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    return float(value) if math.isfinite(value) else None


async def _get_json(client: httpx.AsyncClient, path: str, params: dict | None = None):
    try:
        response = await client.get(
            f"{GIR_BO_BASE_URL}{path}",
            params=params,
            headers={"User-Agent": USER_AGENT, "Referer": f"{GIR_BO_BASE_URL}/"},
        )
    except httpx.HTTPError as exc:
        raise GirBoError(f"bo.nalog.gov.ru недоступен: {exc}") from exc
    if response.status_code in (401, 403, 429, 451):
        raise GirBoBlocked(
            "bo.nalog.gov.ru временно ограничил доступ (защита от частых запросов) — "
            "попробуйте позже"
        )
    if response.status_code != 200:
        raise GirBoError(f"bo.nalog.gov.ru вернул ошибку: HTTP {response.status_code}")
    try:
        return response.json()
    except ValueError as exc:
        raise GirBoError("bo.nalog.gov.ru вернул не-JSON (возможна антибот-страница)") from exc


def pick_organization(search: object, inn: str) -> dict | None:
    """Pure function: the search row whose (tag-stripped) ИНН equals `inn`, or None."""
    rows = require_list_field(
        search, "content", error=GirBoError, label=SOURCE_LABEL, where="поиске"
    )
    for row in rows:
        require_fields(
            row, ("id", "inn"), error=GirBoError, label=SOURCE_LABEL, where="строке поиска"
        )
        if _strip_tags(row["inn"]) == inn:
            return row
    return None


def pick_periods(bfo: object) -> list[dict]:
    """Pure function: the newest `PERIODS_LIMIT` filed periods, one entry per period (the
    most recently updated when a period was refiled), newest first."""
    if not isinstance(bfo, list):
        raise GirBoError(f"{SOURCE_LABEL}: схема ответа изменилась — список периодов не список")
    latest: dict[int, dict] = {}
    for entry in bfo:
        require_fields(
            entry, ("id", "period"), error=GirBoError, label=SOURCE_LABEL, where="периоде"
        )
        try:
            year = int(entry["period"])
        except (TypeError, ValueError) as exc:
            raise GirBoError(
                f"{SOURCE_LABEL}: схема ответа изменилась — period не год ({entry['period']!r})"
            ) from exc
        known = latest.get(year)
        if known is None or str(entry.get("actualBfoDate") or "") >= str(
            known.get("actualBfoDate") or ""
        ):
            latest[year] = entry
    return [latest[y] for y in sorted(latest, reverse=True)[:PERIODS_LIMIT]]


def parse_year(period: dict, detail: object | None) -> dict:
    """Pure function: one period's figures. List-level `gainSum`/`actives` seed revenue and
    assets (so a period whose detail couldn't be fetched still shows something); the detail
    form's lines override them and add the rest."""
    year: dict = {
        "year": int(period["period"]),
        "reported_at": period.get("actualBfoDate"),
        "revenue": _number(period.get("gainSum")),
        "net_profit": None,
        "assets": _number(period.get("actives")),
        "equity": None,
        "current_assets": None,
        "current_liabilities": None,
        "long_term_liabilities": None,
        "cash": None,
        "detail_loaded": False,
    }
    if detail is None:
        return year

    form = detail[0] if isinstance(detail, list) and detail else detail
    require_dict(form, error=GirBoError, label=SOURCE_LABEL, where="детальной форме")
    balance = require_dict(
        form.get("balance"), error=GirBoError, label=SOURCE_LABEL, where="balance формы"
    )
    result = require_dict(
        form.get("financialResult"),
        error=GirBoError,
        label=SOURCE_LABEL,
        where="financialResult формы",
    )
    for lines, section in ((_BALANCE_LINES, balance), (_RESULT_LINES, result)):
        for line, field in lines.items():
            value = _number(section.get(line))
            if value is not None:
                year[field] = value
    year["detail_loaded"] = True
    return year


def _empty_result() -> dict:
    return {
        "checked": False,
        "found": False,
        "has_reports": False,
        "org_name": None,
        "status_code": None,
        "profile_url": None,
        "unit": UNIT,
        "years": [],
        "note": None,
    }


async def fetch_gir_bo_financials(inn: str, *, is_individual: bool) -> tuple[dict, str]:
    """Look up `inn` in ГИР БО and return `(result, raw_payload)`. Individual entrepreneurs
    have no statements there - a checked, empty, explained result without a request."""
    if not inn:
        return _empty_result(), ""
    if is_individual:
        return {
            **_empty_result(),
            "checked": True,
            "note": "У индивидуальных предпринимателей нет бухгалтерской отчётности в ГИР БО",
        }, ""

    raw: dict = {"search": None, "bfo": None, "details": {}}
    async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT_SECONDS, follow_redirects=False) as client:
        search = await _get_json(
            client, "/advanced-search/organizations/search", {"query": inn, "page": 0}
        )
        raw["search"] = search
        org = pick_organization(search, inn)
        result = {**_empty_result(), "checked": True}
        if org is None:
            result["note"] = (
                "Организации нет в ГИР БО (банк, страховщик, не публиковала отчётность)"
            )
            return result, json.dumps(raw, ensure_ascii=False, indent=2)

        result.update(
            found=True,
            org_name=_strip_tags(org.get("shortName")),
            status_code=org.get("statusCode"),
            # The site is an SPA that answers 200 on any path, so a per-organization deep
            # link can't be verified - link the site itself (the report spells the ИНН out).
            profile_url=f"{GIR_BO_BASE_URL}/",
        )
        bfo = await _get_json(client, f"/nbo/organizations/{org['id']}/bfo/")
        raw["bfo"] = bfo
        periods = pick_periods(bfo)
        if not periods:
            result["note"] = "Организация есть в ГИР БО, но опубликованной отчётности нет"
            return result, json.dumps(raw, ensure_ascii=False, indent=2)

        details = await asyncio.gather(
            *(_get_json(client, f"/nbo/bfo/{p['id']}/details") for p in periods),
            return_exceptions=True,
        )

    years: list[dict] = []
    failures: list[str] = []
    for period, detail in zip(periods, details, strict=True):
        if isinstance(detail, GirBoBlocked):
            raise detail
        if isinstance(detail, BaseException) and not isinstance(detail, GirBoError):
            raise detail
        raw["details"][str(period["id"])] = None if isinstance(detail, BaseException) else detail
        if isinstance(detail, GirBoError):
            failures.append(f"{period['period']}: {detail}")
            years.append(parse_year(period, None))
        else:
            years.append(parse_year(period, detail))

    if not any(y["detail_loaded"] for y in years):
        raise GirBoError(
            f"{SOURCE_LABEL}: детальные формы отчётности не получены ({'; '.join(failures)})"
            if failures
            else f"{SOURCE_LABEL}: детальные формы отчётности не получены"
        )
    result["has_reports"] = True
    result["years"] = years
    if failures:
        result["note"] = (
            "Детальная форма получена не за все годы — за остальные показаны только выручка и "
            "активы: " + "; ".join(failures)
        )
    return result, json.dumps(raw, ensure_ascii=False, indent=2)
