"""Local copy of the Банк России list of "companies with signs of illegal activity in the
financial market" (https://www.cbr.ru/inside/warning-list/).

Matched by exact ИНН against a local table, so the ИНН of the entity being checked is never
sent to the regulator, and refreshed by downloading the full list.

**Verified against the live list - 2026-09-28.** Keyless; TLS verifies. `GET
/inside/warning-list/black-list-json` -> `{"RC": [entry...]}` (~10.8 MB, 27 264 entries that
day). Entry keys: `Id`, `DT` (`YYYY-MM-DD`), `Name`, `INN`, `ADDR`, `Site`, `Sign`, `Closed`,
`Comment`, `DateUpdate`, `OrgType`. Only 2 997 entries (11%) carry an ИНН - all 10-digit legal
entities; the rest are websites/"points of presence". What that means for a match:

* It is the regulator's *stated sign* ("признаки нелегального кредитора", "признаки
  финансовой пирамиды", ...), not a court finding - so the flag is soft, worded as the
  regulator's statement.
* "Not on the list" is **not** "clean": the same operator may be listed under another name or
  site with no ИНН - the panel says so.
* `Closed: true` (the regulator marks the organization liquidated) keeps the entry; the sign
  stays a fact.
* A `Comment` that the entry "uses data of a legitimate market participant" marks a *clone*:
  the ИНН owner is the impersonated party. Such a match is shown, never flagged against them.

The list carries no ИНН for individual entrepreneurs (12-digit), so for an ИП the scan records
`not_applicable_result()` instead of a lookup.
The refresh keeps only the ИНН-bearing entries, replaces the table in one transaction, and
refuses a list that looks truncated or has lost its ИНН field (`MIN_TOTAL_ENTRIES`,
`MIN_ENTRIES_WITH_INN`, `MIN_ROW_RATIO`). Fixed host - nothing user-supplied reaches the
request (see backend/tests/core/test_ssrf_guard_coverage.py's ALLOWLISTED_FIXED_HOST_FILES).
"""

import datetime
import json
import logging
import re

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.features.ru_business_check.models.ru_business_check_models import CbrWarningRecord
from app.features.ru_business_check.service.registry_dump_common import (
    INN_RE,
    DumpSource,
    freshness,
    loaded_meta,
    refresh_published_list,
)

logger = logging.getLogger(__name__)

SOURCE_KEY = "cbr_warning"
HOST_PREFIX = "https://www.cbr.ru/"
LIST_URL = "https://www.cbr.ru/inside/warning-list/black-list-json"
PAGE_URL = "https://www.cbr.ru/inside/warning-list/"
LIMIT_BYTES = 100 << 20
# Sanity floors from the 2026-09-28 list (27 264 entries, 2 997 with an ИНН): a smaller list
# is truncated, and one without ИНН values would make every lookup a false "no match".
MIN_TOTAL_ENTRIES = 10_000
MIN_ENTRIES_WITH_INN = 1_500
# The list grows daily; refresh often, and show a lookup as outdated past two weeks.
STALE_AFTER = datetime.timedelta(days=2)
OUTDATED_AFTER = datetime.timedelta(days=14)
CLONE_MARKER = "использует данные легального участника"
MAX_LISTED_RECORDS = 10

_DATE_RE = re.compile(r"\d{4}-\d{2}-\d{2}")
_REQUIRED_KEYS = ("Id", "DT", "Name", "INN", "Sign", "Closed", "Comment", "OrgType")


class CbrWarningError(ValueError):
    """The list couldn't be downloaded, parsed, or isn't loaded yet"""


def parse_list(text: str) -> tuple[list[dict], int]:
    """Pure function: the list JSON -> `(records with a 10-digit ИНН, total entries)`. Any
    deviation from the observed shape is a `CbrWarningError`, never a skipped entry - a
    silently dropped entry with an ИНН would read as "no match" exactly where there is one."""
    try:
        root = json.loads(text)
    except ValueError as exc:
        raise CbrWarningError("список ЦБ: схема ответа изменилась — ответ не JSON") from exc
    entries = root.get("RC") if isinstance(root, dict) else None
    if not isinstance(entries, list):
        raise CbrWarningError("список ЦБ: схема ответа изменилась — нет списка «RC»")

    records: list[dict] = []
    for entry in entries:
        if not isinstance(entry, dict) or any(key not in entry for key in _REQUIRED_KEYS):
            raise CbrWarningError("список ЦБ: схема ответа изменилась — у записи нет ключа")
        inn = entry["INN"]
        if inn in (None, ""):
            continue
        if not isinstance(inn, str) or not INN_RE.fullmatch(inn):
            raise CbrWarningError(f"список ЦБ: схема ответа изменилась — ИНН {str(inn)[:20]!r}")
        if len(inn) != 10:
            continue  # the list carries only legal entities' ИНН; a 12-digit one is not used
        listed = entry["DT"]
        if not isinstance(listed, str) or not _DATE_RE.fullmatch(listed):
            raise CbrWarningError("список ЦБ: схема ответа изменилась — DT не дата")
        if not isinstance(entry["Closed"], bool) or not isinstance(entry["Id"], int):
            raise CbrWarningError("список ЦБ: схема ответа изменилась — типы Id/Closed")
        comment = entry["Comment"] if isinstance(entry["Comment"], str) else None
        try:
            listed_at = datetime.date.fromisoformat(listed)
        except ValueError as exc:
            raise CbrWarningError("список ЦБ: схема ответа изменилась — DT не календарная") from exc
        records.append(
            {
                "cbr_id": entry["Id"],
                "inn": inn,
                "name": (entry["Name"] or None) and str(entry["Name"])[:500],
                "sign": (entry["Sign"] or None) and str(entry["Sign"])[:500],
                "listed_at": listed_at,
                "closed": entry["Closed"],
                "comment": comment[:1000] if comment else None,
                "is_clone": bool(comment and CLONE_MARKER in comment),
            }
        )
    return records, len(entries)


SOURCE = DumpSource(
    key=SOURCE_KEY,
    model=CbrWarningRecord,
    label="Список ЦБ",
    error=CbrWarningError,
    allowed_prefix=HOST_PREFIX,
    limit=LIMIT_BYTES,
    min_total=MIN_TOTAL_ENTRIES,
    min_matchable=MIN_ENTRIES_WITH_INN,
)


async def refresh_list(db: AsyncSession) -> dict:
    """Download the list and replace the local copy all-or-nothing, in the caller's
    transaction (call under `registry_dump_common.refresh_lock(SOURCE_KEY)`); raises
    `CbrWarningError` (old data untouched) on any failure."""
    summary = await refresh_published_list(db, SOURCE, url=LIST_URL, parse=parse_list)
    logger.info("ЦБ warning list refreshed: %s", summary)
    return summary


def not_applicable_result() -> dict:
    """An individual entrepreneur: the list carries only legal entities' (10-digit) ИНН, so
    there is nothing to match. The scan stores this explanation in `extra_data` and lists the
    source as neither checked nor pending."""
    return {
        "checked": True,
        "as_of": None,
        "outdated": False,
        "not_applicable": (
            "Список ЦБ содержит ИНН только юридических лиц — для ИП сверка не применяется"
        ),
        "records": [],
    }


async def lookup_list(db: AsyncSession, inn: str) -> dict:
    """Exact-ИНН match against the local list. Raises `CbrWarningError` when no list is
    loaded (the source is then not-checked, never "clean")."""
    meta = await loaded_meta(db, SOURCE, not_loaded="список ЦБ ещё не загружен")
    rows = (
        (await db.execute(select(CbrWarningRecord).where(CbrWarningRecord.inn == inn)))
        .scalars()
        .all()
    )
    return {
        "checked": True,
        **freshness(meta, OUTDATED_AFTER),
        "records": [
            {
                "cbr_id": r.cbr_id,
                "name": r.name,
                "sign": r.sign,
                "listed_at": r.listed_at.isoformat() if r.listed_at else None,
                "closed": r.closed,
                "comment": r.comment,
                "is_clone": r.is_clone,
            }
            for r in rows[:MAX_LISTED_RECORDS]
        ],
    }
