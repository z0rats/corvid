"""Free-text name/alias search over OpenSanctions' cleaned mirror of the OFAC SDN list.

**Verified against the live file - 2026-09-29.** Keyless; TLS verifies. The stable URL
`https://data.opensanctions.org/datasets/latest/us_ofac_sdn/targets.simple.csv` answers a
single 307 -> a versioned path on the same host (each hop checked, see `is_allowed_redirect`).
20 346 entities that day: Organization 9869, Person 7509, Vessel 1537, Airplane 342, Company 22,
Security 7, LegalEntity 2, CryptoWallet 1058.

Unlike `ru_business_check`'s OFAC consumer (exact Russian ИНН match against a ~3.7k-entry
subset of Treasury's raw SDN CSV), this is the full list, matched by free-text name/alias -
see docs/adr/0017-sanctions-search-opensanctions-and-in-house-matching.md for why these stay
two separate tables/dumps rather than one.

The refresh replaces the whole table in one transaction (`registry_dumps.common.replace_dump`)
and invalidates the in-memory search index so the next search rebuilds it from the fresh rows."""

import datetime
import logging
from urllib.parse import urlparse

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.registry_dumps.common import (
    DumpSource,
    freshness,
    loaded_meta,
    refresh_published_list,
)
from app.features.sanctions_search.models.sanctions_search_models import SanctionsEntry
from app.features.sanctions_search.service.opensanctions_csv_parser import parse_targets_csv
from app.features.sanctions_search.service.search_index import (
    get_index,
    invalidate_index,
    normalize,
)

logger = logging.getLogger(__name__)

SOURCE_KEY = "opensanctions_ofac_sdn"
LIST_URL = "https://data.opensanctions.org/datasets/latest/us_ofac_sdn/targets.simple.csv"
HOST_PREFIX = "https://data.opensanctions.org/datasets/latest/us_ofac_sdn/"
LIMIT_BYTES = 30 << 20
MAX_REDIRECTS = 2
# Sanity floor from the 2026-09-29 list (20 346 entities).
MIN_TOTAL_ENTRIES = 10_000
# Every parsed row is usable (no ИНН-style subset to require a minimum of, unlike
# ru_business_check's dumps) - the total floor above is what actually guards this refresh.
MIN_MATCHABLE_ENTRIES = 0
# OpenSanctions rebuilds this dataset roughly daily; refresh every 2 days like the other OFAC
# mirror, show a lookup as outdated past two weeks.
STALE_AFTER = datetime.timedelta(days=2)
OUTDATED_AFTER = datetime.timedelta(days=14)
MIN_QUERY_LENGTH = 3
DEFAULT_LIMIT = 50
MAX_LIMIT = 200


class SanctionsSearchError(ValueError):
    """The list couldn't be downloaded, parsed, or isn't loaded yet"""


def is_allowed_redirect(url: str) -> bool:
    """A redirect target must be https on OpenSanctions' own host (the CDN answers with a
    versioned `/artifacts/...` path on the same host, not a different one)."""
    parsed = urlparse(url)
    return parsed.scheme == "https" and parsed.hostname == "data.opensanctions.org"


SOURCE = DumpSource(
    key=SOURCE_KEY,
    model=SanctionsEntry,
    label="Список OpenSanctions/OFAC SDN",
    error=SanctionsSearchError,
    allowed_prefix=HOST_PREFIX,
    limit=LIMIT_BYTES,
    redirect_ok=is_allowed_redirect,
    max_redirects=MAX_REDIRECTS,
    min_total=MIN_TOTAL_ENTRIES,
    min_matchable=MIN_MATCHABLE_ENTRIES,
)


async def refresh_list(db: AsyncSession) -> dict:
    """Call under `registry_dumps.common.refresh_lock(SOURCE_KEY)`; raises
    `SanctionsSearchError` on failure, old data left untouched."""
    summary = await refresh_published_list(db, SOURCE, url=LIST_URL, parse=parse_targets_csv)
    invalidate_index()
    logger.info("OpenSanctions OFAC SDN list refreshed: %s", summary)
    return summary


def _rank(query_norm: str, index) -> dict[int, str]:
    """Ranked buckets - exact name, exact alias, substring name, substring alias - deduped by
    id, first match wins so an entry only ever appears once at its best-ranked bucket."""
    matched: dict[int, str] = {}
    for bucket, ids in (
        ("exact_name", index.exact_name.get(query_norm, [])),
        ("exact_alias", index.exact_alias.get(query_norm, [])),
        ("substring_name", [i for name_norm, i in index.all_names if query_norm in name_norm]),
        ("substring_alias", [i for alias_norm, i in index.all_aliases if query_norm in alias_norm]),
    ):
        for entry_id in ids:
            matched.setdefault(entry_id, bucket)
    return matched


async def search(db: AsyncSession, *, query: str, schema: str | None, limit: int) -> dict:
    meta = await loaded_meta(
        db, SOURCE, not_loaded="the OpenSanctions/OFAC SDN list has not been loaded yet"
    )
    query_norm = normalize(query)
    index = await get_index()
    matched = _rank(query_norm, index)

    ids = [
        entry_id for entry_id in matched if schema is None or index.rows[entry_id].schema == schema
    ]
    total_matches = len(ids)
    truncated = total_matches > limit

    matches = []
    for entry_id in ids[:limit]:
        row = index.rows[entry_id]
        matches.append(
            {
                "opensanctions_id": row.opensanctions_id,
                "schema": row.schema,
                "name": row.name,
                "aliases": row.aliases,
                "countries": row.countries,
                "programs": row.programs,
                "sanctions": row.sanctions,
                "first_seen": row.first_seen,
                "last_seen": row.last_seen,
                "matched_on": matched[entry_id],
            }
        )

    return {
        "query": query,
        "schema_filter": schema,
        **freshness(meta, OUTDATED_AFTER),
        "matches": matches,
        "total_matches": total_matches,
        "truncated": truncated,
    }


async def list_schemas() -> list[str]:
    index = await get_index()
    return index.schemas
