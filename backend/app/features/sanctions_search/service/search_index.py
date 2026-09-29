"""In-memory name/alias search index over `SanctionsEntry`, rebuilt from the DB on first use
and cached event-drivenly (see `TtlCache`) - `refresh_list()` calls `invalidate_index()` right
after its own DB replace commits, so the next search rebuilds it; a freshly restarted process
lazily builds it on its own first `get_index()`. A linear scan over ~20k short normalized
strings is sub-50ms in pure Python, cheap enough that a DB-side full-text mechanism (e.g.
SQLite FTS5) isn't worth the extra moving part - see docs/adr/0017-*.md."""

import re
import unicodedata
from dataclasses import dataclass, field

from sqlalchemy import select

from app.core.database import managed_session
from app.core.utils.ttl_cache import TtlCache
from app.features.sanctions_search.models.sanctions_search_models import SanctionsEntry

_PUNCTUATION_RE = re.compile(r"[^\w\s]", re.UNICODE)
_WHITESPACE_RE = re.compile(r"\s+")


def normalize(value: str) -> str:
    """Lowercase, strip accents/punctuation, collapse whitespace - applied identically to
    indexed names/aliases and incoming queries so the same string always yields the same key."""
    folded = unicodedata.normalize("NFKD", value.casefold())
    folded = "".join(ch for ch in folded if not unicodedata.combining(ch))
    stripped = _PUNCTUATION_RE.sub(" ", folded)
    return _WHITESPACE_RE.sub(" ", stripped).strip()


@dataclass(frozen=True)
class SanctionsRow:
    id: int
    opensanctions_id: str
    schema: str
    name: str
    aliases: list
    countries: list
    programs: list
    sanctions: str | None
    first_seen: object | None
    last_seen: object | None


@dataclass(frozen=True)
class Index:
    rows: dict[int, SanctionsRow] = field(default_factory=dict)
    exact_name: dict[str, list[int]] = field(default_factory=dict)
    exact_alias: dict[str, list[int]] = field(default_factory=dict)
    all_names: list[tuple[str, int]] = field(default_factory=list)
    all_aliases: list[tuple[str, int]] = field(default_factory=list)
    schemas: list[str] = field(default_factory=list)


async def _build_index() -> Index:
    rows: dict[int, SanctionsRow] = {}
    exact_name: dict[str, list[int]] = {}
    exact_alias: dict[str, list[int]] = {}
    all_names: list[tuple[str, int]] = []
    all_aliases: list[tuple[str, int]] = []
    schemas: set[str] = set()

    async with managed_session() as db:
        result = await db.execute(select(SanctionsEntry))
        for entry in result.scalars():
            rows[entry.id] = SanctionsRow(
                id=entry.id,
                opensanctions_id=entry.opensanctions_id,
                schema=entry.schema,
                name=entry.name,
                aliases=entry.aliases,
                countries=entry.countries,
                programs=entry.programs,
                sanctions=entry.sanctions,
                first_seen=entry.first_seen,
                last_seen=entry.last_seen,
            )
            schemas.add(entry.schema)
            name_norm = normalize(entry.name)
            if name_norm:
                exact_name.setdefault(name_norm, []).append(entry.id)
                all_names.append((name_norm, entry.id))
            for alias in entry.aliases:
                alias_norm = normalize(alias)
                if alias_norm:
                    exact_alias.setdefault(alias_norm, []).append(entry.id)
                    all_aliases.append((alias_norm, entry.id))

    return Index(
        rows=rows,
        exact_name=exact_name,
        exact_alias=exact_alias,
        all_names=all_names,
        all_aliases=all_aliases,
        schemas=sorted(schemas),
    )


_index_cache: TtlCache[Index] = TtlCache(fetch=_build_index, ttl_seconds=float("inf"))


def invalidate_index() -> None:
    _index_cache.invalidate()


async def get_index() -> Index:
    return await _index_cache.get()
