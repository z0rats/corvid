"""Scraper for service.nalog.ru/disqualified.do - the official (keyless) registry of
disqualified persons (РДЛ).

Fixed host, only the searched full name is user-supplied - never the host - so this
intentionally does NOT go through app.core.security.ssrf_guard.safe_get (see
backend/tests/core/test_ssrf_guard_coverage.py's ALLOWLISTED_FIXED_HOST_FILES).

**Verified against a live capture - 2026-09-28.** The search page's own `<form>` posts to
`disqualified-proc.json`, which answers with **JSON**, not an HTML table:
`{"data": [row...], "rowCount": N, "pageSize": 25, ...}` with Russian-keyed rows
(`ФИО`, `ДатаРожд`, `МестоРожд`, `НомЗап`, `НаимОрг`, `Должность`, `КвалификацияТекст`,
`НаимОргПрот`, `ФИОСуд`, `ДисквСрок`, `ДатаНачДискв`, `ДатаКонДискв`); `data: []` is the
"no matches" answer. `parse_results` reads that JSON, still accepts an HTML results table,
and treats any other answer as a `DisqualifiedPersonsError` - never as an empty result. The
form field name isn't hardcoded: `_discover_search_field` reads the live search page's own
`<form>` markup.

Per project decision, a name-only match here is NEVER treated as a confirmed hard flag -
even with the registry's date of birth shown, the ЕГРЮЛ extract carries no director birth
date to compare it with, so a same-name collision can't be ruled out here; every match is
surfaced as `requires_manual_review`, with the registry's birth date to help the analyst.
"""

import json
import logging
from urllib.parse import urljoin

import httpx
from bs4 import BeautifulSoup

from app.features.ru_business_check.service.source_contract import (
    require_fields,
    require_list_field,
)

logger = logging.getLogger(__name__)

DISQUALIFIED_PERSONS_URL = "https://service.nalog.ru/disqualified.do"
REQUEST_TIMEOUT_SECONDS = 20.0


class DisqualifiedPersonsError(ValueError):
    """The service itself failed/timed out, or its form shape couldn't be parsed"""


def _discover_search_field(html: str) -> tuple[str, str, dict[str, str]]:
    """Return (method, action_url, hidden_fields) plus, separately, the name of the
    first visible text input - read from the live page rather than hardcoded, since the
    real field name hasn't been confirmed against a live capture."""
    soup = BeautifulSoup(html, "lxml")
    form = soup.find("form")
    if form is None:
        raise DisqualifiedPersonsError("Не удалось найти форму поиска на странице РДЛ")

    method = (form.get("method") or "get").lower()
    action = urljoin(DISQUALIFIED_PERSONS_URL, form.get("action") or "")

    hidden_fields: dict[str, str] = {}
    query_field: str | None = None
    for tag in form.find_all("input"):
        name = tag.get("name")
        if not name:
            continue
        input_type = (tag.get("type") or "text").lower()
        if input_type == "hidden":
            hidden_fields[name] = tag.get("value", "")
        elif input_type in ("text", "search") and query_field is None:
            query_field = name

    if query_field is None:
        raise DisqualifiedPersonsError("Не удалось определить поле поиска на странице РДЛ")

    return method, action, {**hidden_fields, "__query_field__": query_field}


_RESULT_COLUMNS = [
    "record_number",
    "full_name",
    "organization_position",
    "article",
    "issuing_authority",
    "judge",
    "details",
]


def parse_results_html(html: str) -> list[dict]:
    """Pure function: extract disqualified-person rows from the results page.
    Kept separate from the network code above so it's independently unit-testable.

    Column order follows the page's own header row (Номер записи РДЛ / Дисквалифицированное
    лицо / Организация, должность / Статья КоАП РФ / Наименование органа / Судья / Сведения
    о дисквалификации) - the leading "№ п/п" serial column is dropped, it carries no data.
    """
    soup = BeautifulSoup(html, "lxml")
    table = soup.find("table")
    if table is None:
        return []

    rows: list[dict] = []
    for tr in table.find_all("tr"):
        cells = [td.get_text(strip=True) for td in tr.find_all("td")]
        if len(cells) < len(_RESULT_COLUMNS) + 1:
            continue  # header row or a row without enough columns to be a data row
        cells = cells[1:]  # drop the "№ п/п" serial column
        record = dict(zip(_RESULT_COLUMNS, cells, strict=False))
        if not record.get("full_name"):
            continue
        organization_position = record.pop("organization_position", "")
        organization, _, position = organization_position.partition(",")
        rows.append(
            {
                "full_name": record["full_name"],
                "record_number": record.get("record_number") or None,
                "organization": organization.strip() or None,
                "position": position.strip() or None,
                "article": record.get("article") or None,
                "issuing_authority": record.get("issuing_authority") or None,
                "judge": record.get("judge") or None,
                "details": record.get("details") or None,
            }
        )
    return rows


def _date_part(value: object) -> str | None:
    """`DD.MM.YYYY HH:MM:SS` -> `DD.MM.YYYY`; anything else is dropped rather than shown."""
    if isinstance(value, str) and len(value) >= 10 and value[2] == "." and value[5] == ".":
        return value[:10]
    return None


def parse_results_json(payload: dict) -> list[dict]:
    """Pure function: the `disqualified-proc.json` payload -> match rows (same shape as
    `parse_results_html`, plus `birth_date`). Raises `DisqualifiedPersonsError` on drift."""
    rows = require_list_field(
        payload,
        "data",
        error=DisqualifiedPersonsError,
        label="РДЛ",
    )
    matches: list[dict] = []
    for row in rows:
        require_fields(
            row,
            ("ФИО", "НомЗап"),
            error=DisqualifiedPersonsError,
            label="РДЛ",
            where="записи реестра",
        )
        if not row["ФИО"]:
            continue
        term = " ".join(
            part
            for part in (
                f"срок: {row['ДисквСрок']}" if row.get("ДисквСрок") else "",
                f"с {_date_part(row.get('ДатаНачДискв'))}"
                if _date_part(row.get("ДатаНачДискв"))
                else "",
                f"по {_date_part(row.get('ДатаКонДискв'))}"
                if _date_part(row.get("ДатаКонДискв"))
                else "",
            )
            if part
        )
        matches.append(
            {
                "full_name": row["ФИО"],
                "record_number": str(row["НомЗап"]) if row.get("НомЗап") else None,
                "organization": row.get("НаимОрг") or None,
                "position": row.get("Должность") or None,
                "article": row.get("КвалификацияТекст") or None,
                "issuing_authority": row.get("НаимОргПрот") or None,
                "judge": row.get("ФИОСуд") or None,
                "details": term or None,
                "birth_date": _date_part(row.get("ДатаРожд")),
            }
        )
    return matches


def parse_results(text: str) -> list[dict]:
    """The registry's answer -> match rows. JSON first (what the live site returns), an HTML
    table as a fallback; anything else is drift - an empty list means "the registry said
    no matches", never "I couldn't read the answer"."""
    try:
        payload = json.loads(text)
    except ValueError:
        payload = None
    if isinstance(payload, dict):
        return parse_results_json(payload)
    if "<table" in text:
        return parse_results_html(text)
    raise DisqualifiedPersonsError(
        "РДЛ: схема ответа изменилась — ответ не JSON и без таблицы результатов"
    )


async def check_disqualified(full_name: str) -> tuple[dict, str]:
    """Search the disqualified-persons registry for `full_name` and return
    `(result, raw_payload)`, where `result` is `{checked, matched, requires_manual_review,
    matches}` and `raw_payload` is the verbatim results-page HTML.
    """
    if not full_name or not full_name.strip():
        return {
            "checked": False,
            "matched": False,
            "requires_manual_review": False,
            "matches": [],
        }, ""

    async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT_SECONDS, follow_redirects=False) as client:
        page = await client.get(DISQUALIFIED_PERSONS_URL)
        page.raise_for_status()
        method, action, fields = _discover_search_field(page.text)
        query_field = fields.pop("__query_field__")

        request_params = {**fields, query_field: full_name}
        if method == "post":
            response = await client.post(action, data=request_params)
        else:
            response = await client.get(action, params=request_params)
        response.raise_for_status()

    matches = parse_results(response.text)
    result = {
        "checked": True,
        "matched": bool(matches),
        # Never auto-confirmed - see module docstring for why.
        "requires_manual_review": bool(matches),
        "matches": matches,
    }
    return result, response.text
