"""Parses OpenSanctions' `us_ofac_sdn` `targets.simple.csv` mirror of the OFAC SDN list into
`SanctionsEntry`-shaped records.

Verified against the live file on 2026-09-29: 20346 rows, RFC4180-quoted, no BOM, columns
`id,schema,name,aliases,birth_date,countries,addresses,identifiers,sanctions,phones,emails,
program_ids,dataset,first_seen,last_seen,last_change` (only the ones this feature needs are
read; extra columns are ignored rather than rejected, so an upstream addition doesn't break
the refresh). `first_seen`/`last_seen` are always a full `YYYY-MM-DDTHH:MM:SS` timestamp in
every observed row - truncated to a date, since only the day matters for display. Schema values
observed: Organization (9869), Person (7509), Vessel (1537), Airplane (342), Company (22),
Security (7), LegalEntity (2), CryptoWallet (1058)."""

import csv
import datetime
import io

REQUIRED_COLUMNS = {
    "id",
    "schema",
    "name",
    "aliases",
    "countries",
    "sanctions",
    "program_ids",
    "first_seen",
    "last_seen",
}


class OpenSanctionsCsvError(ValueError):
    pass


def _split_multi(value: str) -> list[str]:
    seen: dict[str, None] = {}
    for part in value.split(";"):
        stripped = part.strip()
        if stripped:
            seen.setdefault(stripped, None)
    return list(seen)


def _parse_date(value: str) -> datetime.date | None:
    if not value:
        return None
    try:
        return datetime.datetime.fromisoformat(value).date()
    except ValueError:
        return None


def parse_targets_csv(text: str) -> tuple[list[dict], int]:
    """Returns `(records, total)` - every row parses into a record here (unlike
    ru_business_check's ИНН-filtered dumps, there is no subset of "non-matchable" rows), so
    `total == len(records)` unless a row is missing its `name`/`id`."""
    reader = csv.DictReader(io.StringIO(text))
    fieldnames = set(reader.fieldnames or [])
    if not REQUIRED_COLUMNS.issubset(fieldnames):
        missing = REQUIRED_COLUMNS - fieldnames
        raise OpenSanctionsCsvError(
            f"OpenSanctions CSV schema changed — missing columns: {sorted(missing)}"
        )

    records: list[dict] = []
    total = 0
    for row in reader:
        total += 1
        opensanctions_id = (row.get("id") or "").strip()
        name = (row.get("name") or "").strip()
        if not opensanctions_id or not name:
            continue
        records.append(
            {
                "opensanctions_id": opensanctions_id[:64],
                "schema": (row.get("schema") or "").strip()[:30],
                "name": name[:500],
                "aliases": _split_multi(row.get("aliases") or ""),
                "countries": _split_multi(row.get("countries") or ""),
                "programs": _split_multi(row.get("program_ids") or ""),
                "sanctions": (row.get("sanctions") or "").strip()[:2000] or None,
                "first_seen": _parse_date((row.get("first_seen") or "").strip()),
                "last_seen": _parse_date((row.get("last_seen") or "").strip()),
            }
        )
    return records, total
