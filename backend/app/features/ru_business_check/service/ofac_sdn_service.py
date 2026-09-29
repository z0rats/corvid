"""Local copy of the US Treasury OFAC **SDN** (Specially Designated Nationals) list, matched
by exact Russian ИНН.

Why by ИНН: OFAC's records for Russian entities carry `Tax ID No. <ИНН> (Russia)` in their
remarks, so a company can be matched to the list exactly - no fuzzy name matching, no
transliteration guesswork - and locally, so the ИНН is never sent to a third party.

**Verified against the live list - 2026-09-28.** Keyless; TLS verifies. The stable URL
`https://www.treasury.gov/ofac/downloads/sdn.csv` answers 302 -> `sanctionslistservice.
ofac.treas.gov/api/publicationpreview/exports/sdn.csv` -> 302 -> a short-lived signed URL on
`*.s3.us-gov-west-1.amazonaws.com` (each hop is checked, see `is_allowed_redirect`). The file
(~5.7 MB, utf-8, ends with a stray 0x1A) is the legacy 12-column, header-less CSV:
`ent_num, SDN_Name, SDN_Type, Program, Title, Call_Sign, Vess_type, Tonnage, GRT,
Vess_flag, Vess_owner, Remarks`; `SDN_Type` is `-0-` for an entity, else `individual`/
`vessel`/`aircraft`. 19 391 entries that day, 3 728 with `Tax ID No. ... (Russia)` (3 275
ten-digit entities, 455 twelve-digit individuals - an ИП can match too).

What a match means: the entity is on the SDN list. That's a US sanctions status - a hard fact
about the list, not a Russian-law prohibition - so the flag is worded as exactly that. The
SDN list is only one US list (no non-SDN/sectoral lists) and OFAC ownership rules (the "50
percent rule") reach entities that are not listed themselves: absence here is **not** "no
sanctions exposure". The EU consolidated list isn't included (checked 2026-09-28: its CSV
export answers 403 without a token, and none of its 43 891 rows carries a 10/12-digit
identification number - it could only be matched by name).

The refresh keeps only entries with a Russian ИНН, replaces the table in one transaction, and
refuses a list that looks truncated or has lost that remark (`MIN_TOTAL_ENTRIES`,
`MIN_ENTRIES_WITH_INN`, `MIN_ROW_RATIO`). Fixed hosts only - nothing user-supplied reaches the
request (see backend/tests/core/test_ssrf_guard_coverage.py's ALLOWLISTED_FIXED_HOST_FILES).
"""

import csv
import datetime
import io
import logging
import re
from urllib.parse import urlparse

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.registry_dumps.common import (
    DumpSource,
    freshness,
    loaded_meta,
    refresh_published_list,
)
from app.features.ru_business_check.models.ru_business_check_models import OfacSdnRecord

logger = logging.getLogger(__name__)

SOURCE_KEY = "ofac_sdn"
LIST_URL = "https://www.treasury.gov/ofac/downloads/sdn.csv"
HOST_PREFIX = "https://www.treasury.gov/ofac/downloads/"
LIST_PAGE_URL = "https://sanctionssearch.ofac.treas.gov/"
LIMIT_BYTES = 100 << 20
MAX_REDIRECTS = 3
# Sanity floors from the 2026-09-28 list (19 391 entries, 3 728 with a Russian ИНН).
MIN_TOTAL_ENTRIES = 10_000
MIN_ENTRIES_WITH_INN = 1_500
# OFAC republishes a few times a week; refresh often, show a lookup as outdated past two weeks.
STALE_AFTER = datetime.timedelta(days=2)
OUTDATED_AFTER = datetime.timedelta(days=14)
MAX_LISTED_RECORDS = 10

_COLUMNS = 12
_RU_INN_RE = re.compile(r"Tax ID No\. (\d{10}|\d{12}) \(Russia\)")
_ALLOWED_REDIRECT_HOSTS = {"www.treasury.gov", "sanctionslistservice.ofac.treas.gov"}
_STORAGE_SUFFIX = ".s3.us-gov-west-1.amazonaws.com"


class OfacSdnError(ValueError):
    """The list couldn't be downloaded, parsed, or isn't loaded yet"""


def is_allowed_redirect(url: str) -> bool:
    """A redirect target must be https on OFAC's own hosts or its published-file storage."""
    parsed = urlparse(url)
    host = parsed.hostname or ""
    return parsed.scheme == "https" and (
        host in _ALLOWED_REDIRECT_HOSTS or host.endswith(_STORAGE_SUFFIX)
    )


def parse_sdn(text: str) -> tuple[list[dict], int]:
    """Pure function: the SDN CSV -> `(records with a Russian ИНН, total entries)`. Any row
    that isn't the observed 12 columns is an `OfacSdnError`, never a skipped entry - a
    silently dropped entry would read as "not listed" exactly where it is."""
    records: list[dict] = []
    total = 0
    for row in csv.reader(io.StringIO(text.lstrip("﻿"))):
        if not row or row == ["\x1a"]:
            continue  # blank line / the file's trailing EOF marker
        if len(row) != _COLUMNS:
            raise OfacSdnError(
                f"список OFAC: схема ответа изменилась — строка из {len(row)} колонок"
            )
        try:
            ent_num = int(row[0])
        except ValueError as exc:
            raise OfacSdnError(
                "список OFAC: схема ответа изменилась — номер записи не число"
            ) from exc
        total += 1
        kind = "entity" if row[2].strip() == "-0-" else row[2].strip().lower()
        programs = row[3].strip()
        for inn in dict.fromkeys(_RU_INN_RE.findall(row[11])):
            records.append(
                {
                    "ent_num": ent_num,
                    "inn": inn,
                    "name": row[1].strip()[:500],
                    "kind": kind[:20],
                    "programs": (programs if programs != "-0-" else "")[:500] or None,
                }
            )
    return records, total


SOURCE = DumpSource(
    key=SOURCE_KEY,
    model=OfacSdnRecord,
    label="Список OFAC",
    error=OfacSdnError,
    allowed_prefix=HOST_PREFIX,
    limit=LIMIT_BYTES,
    redirect_ok=is_allowed_redirect,
    max_redirects=MAX_REDIRECTS,
    min_total=MIN_TOTAL_ENTRIES,
    min_matchable=MIN_ENTRIES_WITH_INN,
)


async def refresh_list(db: AsyncSession) -> dict:
    """Download the SDN list and replace the local copy all-or-nothing, in the caller's
    transaction (call under `registry_dumps.common.refresh_lock(SOURCE_KEY)`); raises
    `OfacSdnError` (old data untouched) on any failure."""
    summary = await refresh_published_list(db, SOURCE, url=LIST_URL, parse=parse_sdn)
    logger.info("OFAC SDN list refreshed: %s", summary)
    return summary


async def lookup_list(db: AsyncSession, inn: str) -> dict:
    """Exact-ИНН match against the local SDN copy. Raises `OfacSdnError` when no list is
    loaded (the source is then not-checked, never "not sanctioned")."""
    meta = await loaded_meta(db, SOURCE, not_loaded="список OFAC ещё не загружен")
    rows = (await db.execute(select(OfacSdnRecord).where(OfacSdnRecord.inn == inn))).scalars().all()
    return {
        "checked": True,
        **freshness(meta, OUTDATED_AFTER),
        "records": [
            {"ent_num": r.ent_num, "name": r.name, "kind": r.kind, "programs": r.programs}
            for r in rows[:MAX_LISTED_RECORDS]
        ],
    }
