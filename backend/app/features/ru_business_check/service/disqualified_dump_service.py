"""Local copy of the ФНС open-data disqualified-persons register (data.nalog.ru).

The online search (`disqualified_persons_service.py`) can only match by ФИО, so a hit is
always a "check manually" soft flag. The published dataset carries one more identifier for
about a third of its records - the ИНН of the organization the person was disqualified in -
so with a local copy a scan can tell "this exact person, for this exact company, in force
today" (a hard flag) from a mere namesake, and can list the company's own disqualified
officers. It is also a fallback when service.nalog.ru is down.

**Verified against the live dataset - 2026-09-28.** Keyless, no CAPTCHA; the TLS chain
verifies against the standard trust store. `GET <portal>/meta.csv` (`property,value` rows)
lists every published version as `data-YYYYMMDD-structure-*.csv` -> URL, plus `valid`
(YYYYMMDD); the newest `data-` row is the current one. The CSV (utf-8-sig, ~3.5 MB, 8 154
rows that day) has header `G1..G14`: G1 record number, G2 ФИО, G3 birth date, G4 birthplace,
G5 organization, G6 organization ИНН (present on 2 947 rows = 36%), G7 position, G8 КоАП
article, G9 protocol body, G10 judge, G11 judge's position, G12 term, G13 start, G14 end
(`DD.MM.YYYY`). G3/G4/G9-G11 are deliberately not stored.

The refresh replaces the whole table in one transaction (`registry_dumps.common.replace_dump`);
a new version with fewer than half the previous row count is rejected as suspected
truncation/drift and the old data stays.
Fixed host (`PORTAL`), every URL taken from `meta.csv` is checked to be under it, so nothing
user-supplied reaches the request - see backend/tests/core/test_ssrf_guard_coverage.py's
ALLOWLISTED_FIXED_HOST_FILES.
"""

import csv
import datetime
import io
import logging
import re

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.registry_dumps.common import (
    INN_RE,
    DumpSource,
    download_text,
    dump_client,
    loaded_meta,
    replace_dump,
)
from app.features.ru_business_check.models.ru_business_check_models import DisqualifiedRecord

logger = logging.getLogger(__name__)

SOURCE_KEY = "disqualified"
PORTAL = "https://data.nalog.ru/opendata/7707329152-registerdisqualified"
META_LIMIT_BYTES = 1 << 20
CSV_LIMIT_BYTES = 64 << 20
EXPECTED_HEADER = [f"G{i}" for i in range(1, 15)]
# The dataset is republished weekly; re-fetch after this long.
STALE_AFTER = datetime.timedelta(days=7)
MAX_LISTED_RECORDS = 20

_DATA_KEY_RE = re.compile(r"data-(\d{4})(\d{2})(\d{2})-")


class DisqualifiedDumpError(ValueError):
    """The dump couldn't be downloaded, parsed, or isn't loaded yet"""


def normalize_name(name: str | None) -> str:
    """Upper case, ё->е, single spaces - the same folding for stored and searched names."""
    return " ".join(str(name or "").replace("ё", "е").replace("Ё", "Е").upper().split())


def _parse_date(value: str) -> datetime.date:
    match = re.fullmatch(r"(\d{2})\.(\d{2})\.(\d{4})", value.strip())
    if not match:
        raise DisqualifiedDumpError(
            f"схема выгрузки изменилась — дата {value[:20]!r} не в формате ДД.ММ.ГГГГ"
        )
    try:
        return datetime.date(int(match[3]), int(match[2]), int(match[1]))
    except ValueError as exc:
        raise DisqualifiedDumpError(
            f"схема выгрузки изменилась — дата {value[:20]!r} не календарная"
        ) from exc


def parse_meta(text: str) -> tuple[str, datetime.date, datetime.date | None]:
    """Pure function: `meta.csv` -> `(newest data URL, its dataset date, valid-until)`."""
    rows = {
        row[0].strip(): row[1].strip()
        for row in csv.reader(io.StringIO(text.lstrip("﻿")))
        if len(row) >= 2
    }
    versions = sorted(
        ((m.group(0), m, url) for key, url in rows.items() if (m := _DATA_KEY_RE.match(key))),
        key=lambda version: version[0],
    )
    if not versions:
        raise DisqualifiedDumpError("схема выгрузки изменилась — в meta.csv нет ссылок на данные")
    _, m, url = versions[-1]
    if not url.startswith(PORTAL + "/"):
        raise DisqualifiedDumpError(f"адрес выгрузки вне набора открытых данных ФНС: {url[:80]}")
    dump_date = datetime.date(int(m[1]), int(m[2]), int(m[3]))
    valid = re.fullmatch(r"(\d{4})(\d{2})(\d{2})", rows.get("valid", ""))
    valid_until = datetime.date(int(valid[1]), int(valid[2]), int(valid[3])) if valid else None
    return url, dump_date, valid_until


def parse_dump(text: str) -> list[dict]:
    """Pure function: the CSV text -> record dicts (`DisqualifiedRecord` columns). Any
    deviation from the observed shape is a `DisqualifiedDumpError`, never a silent skip."""
    reader = csv.reader(io.StringIO(text.lstrip("﻿")))
    header = [h.strip() for h in next(reader, [])]
    if header != EXPECTED_HEADER:
        raise DisqualifiedDumpError(
            f"схема выгрузки изменилась — заголовок {header[:16]!r} вместо G1..G14"
        )
    records: list[dict] = []
    for row in reader:
        if not any(cell.strip() for cell in row):
            continue
        if len(row) != len(EXPECTED_HEADER):
            raise DisqualifiedDumpError(
                f"схема выгрузки изменилась — строка из {len(row)} колонок вместо 14"
            )
        row = [cell.strip() for cell in row]
        if not row[0] or not row[1]:
            raise DisqualifiedDumpError("схема выгрузки изменилась — запись без номера или ФИО")
        records.append(
            {
                "record_number": row[0][:20],
                "full_name": normalize_name(row[1])[:300],
                "org_name": row[4][:500] or None,
                "org_inn": row[5] if INN_RE.fullmatch(row[5]) else None,
                "position": row[6][:300] or None,
                "article": row[7][:300] or None,
                "term": row[11][:50] or None,
                "start_date": _parse_date(row[12]),
                "end_date": _parse_date(row[13]),
            }
        )
    return records


SOURCE = DumpSource(
    key=SOURCE_KEY,
    model=DisqualifiedRecord,
    label="Выгрузка РДЛ",
    error=DisqualifiedDumpError,
    allowed_prefix=PORTAL + "/",
    limit=CSV_LIMIT_BYTES,
)


async def refresh_dump(db: AsyncSession) -> dict:
    """Download the newest dataset version and replace the local copy, all-or-nothing, in
    the caller's transaction. Raises `DisqualifiedDumpError` (old data untouched) on any
    failure. Call under `registry_dumps.common.refresh_lock(SOURCE_KEY)`."""
    async with dump_client() as client:
        meta_text = await download_text(
            client, f"{PORTAL}/meta.csv", SOURCE, limit=META_LIMIT_BYTES
        )
        url, dump_date, valid_until = parse_meta(meta_text)
        csv_text = await download_text(client, url, SOURCE)
    records = parse_dump(csv_text)
    await replace_dump(db, SOURCE, records, dump_date=dump_date, valid_until=valid_until, url=url)
    summary = {"rows": len(records), "dump_date": dump_date.isoformat(), "url": url}
    logger.info("Disqualified-persons dump refreshed: %s", summary)
    return summary


def _record_view(record: DisqualifiedRecord, today: datetime.date, inn: str) -> dict:
    return {
        "record_number": record.record_number,
        "full_name": record.full_name,
        "org_name": record.org_name,
        "org_inn": record.org_inn,
        "position": record.position,
        "article": record.article,
        "term": record.term,
        "start_date": record.start_date.isoformat(),
        "end_date": record.end_date.isoformat(),
        "active": record.start_date <= today <= record.end_date,
        "same_company": record.org_inn == inn,
    }


async def lookup_dump(
    db: AsyncSession,
    inn: str,
    director_name: str | None,
    *,
    today: datetime.date | None = None,
) -> dict:
    """Match against the local dump: the director by ФИО, and the company by ИНН. Raises
    `DisqualifiedDumpError` when no dump is loaded (the source is then not-checked, never
    "clean")."""
    today = today or datetime.datetime.now(datetime.UTC).date()
    meta = await loaded_meta(
        db, SOURCE, not_loaded="выгрузка реестра дисквалифицированных ещё не загружена"
    )

    name_matches: list[DisqualifiedRecord] = []
    normalized = normalize_name(director_name)
    if normalized:
        name_matches = list(
            (
                await db.execute(
                    select(DisqualifiedRecord).where(DisqualifiedRecord.full_name == normalized)
                )
            )
            .scalars()
            .all()
        )
    company_records = list(
        (await db.execute(select(DisqualifiedRecord).where(DisqualifiedRecord.org_inn == inn)))
        .scalars()
        .all()
    )

    # Confirming records (in force, this company) first, so the listed slice - and the hard
    # flag's citation - always includes one when `director_confirmed` is true.
    director_records = sorted(
        (_record_view(r, today, inn) for r in name_matches),
        key=lambda r: not (r["active"] and r["same_company"]),
    )
    return {
        "checked": True,
        "dump_date": meta.dump_date.isoformat(),
        "valid_until": meta.valid_until.isoformat() if meta.valid_until else None,
        "outdated": bool(meta.valid_until and meta.valid_until < today),
        # The same person, for this very company, in force today: ФИО + ИНН организации.
        "director_confirmed": any(r["active"] and r["same_company"] for r in director_records),
        "director_records": director_records[:MAX_LISTED_RECORDS],
        "company_records": [_record_view(r, today, inn) for r in company_records][
            :MAX_LISTED_RECORDS
        ],
    }
