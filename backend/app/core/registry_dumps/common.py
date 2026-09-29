"""Plumbing shared by every locally cached registry dump (`ru_business_check`'s
disqualified-persons dump, ЦБ warning list, OFAC SDN; `sanctions_search`'s OpenSanctions
mirror; ...): a size-capped download from a fixed host, the all-or-nothing table replacement,
the `RegistryDump` provenance row, and the per-source refresh lock - so each dump service holds
only its own parsing and lookup."""

import asyncio
import datetime
import re
from collections.abc import Callable
from dataclasses import dataclass

import httpx
from sqlalchemy import delete, insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import Base
from app.core.models.registry_dump import RegistryDump

USER_AGENT = "Corvid-OSINT (self-hosted analyst tool)"
DOWNLOAD_TIMEOUT_SECONDS = 120.0
INSERT_CHUNK = 1000
# A new version smaller than this fraction of the loaded one is treated as truncated/broken.
MIN_ROW_RATIO = 0.5
INN_RE = re.compile(r"\d{10}|\d{12}")

_refresh_locks: dict[str, asyncio.Lock] = {}


@dataclass(frozen=True)
class DumpSource:
    """Everything the shared plumbing needs to know about one dump."""

    key: str  # `RegistryDump.source` and the refresh-lock key
    model: type[Base]  # the table holding the matchable records
    label: str  # human name used in error messages
    error: type[ValueError]  # the dump service's own error class
    allowed_prefix: str  # every downloaded URL must start with this (fixed host/path)
    limit: int  # download size cap, bytes
    # Redirects are refused unless a predicate vets each hop.
    redirect_ok: Callable[[str], bool] | None = None
    max_redirects: int = 0
    # Sanity floors for a list published as one live file (see `check_list_floors`).
    min_total: int = 0
    min_matchable: int = 0


def dump_client() -> httpx.AsyncClient:
    """The one HTTP client construction for every dump download (fixed hosts only - see
    `download_text`), never following redirects on its own."""
    return httpx.AsyncClient(timeout=DOWNLOAD_TIMEOUT_SECONDS, follow_redirects=False)


def refresh_lock(source: str) -> asyncio.Lock:
    """The process-wide lock serializing refreshes of one dump. It must cover the whole
    refresh *including the commit*: two overlapping "delete all + insert" transactions would
    duplicate rows (the second DELETE can't see the first one's uncommitted inserts) or
    collide on the `RegistryDump` primary key on a first load."""
    return _refresh_locks.setdefault(source, asyncio.Lock())


async def download_text(
    client: httpx.AsyncClient, url: str, source: DumpSource, *, limit: int | None = None
) -> str:
    """GET `url` (must start with `source.allowed_prefix` - the fixed host/path this dump
    lives under) and return its text, refusing anything over `limit` (default
    `source.limit`) bytes. Every failure is the source's own error class.

    Redirects are never followed blindly (the client has `follow_redirects=False`): with
    `source.redirect_ok`, up to `source.max_redirects` hops are followed manually, each
    target checked against that predicate first - for a publisher that serves the file from
    a signed storage URL behind one or two redirects."""
    error, label = source.error, source.label
    limit = source.limit if limit is None else limit
    redirect_ok = source.redirect_ok
    if not url.startswith(source.allowed_prefix):
        raise error(f"адрес вне ожидаемого источника: {url[:80]}")
    current = url
    for _ in range(source.max_redirects + 1):
        chunks: list[bytes] = []
        total = 0
        try:
            async with client.stream(
                "GET", current, headers={"User-Agent": USER_AGENT}
            ) as response:
                if response.status_code in (301, 302, 303, 307, 308):
                    location = response.headers.get("location")
                    if not location or redirect_ok is None:
                        raise error(f"{label} вернул HTTP {response.status_code}")
                    current = str(httpx.URL(current).join(location))
                    if not redirect_ok(current):
                        raise error(f"{label}: перенаправление на неожиданный адрес")
                    continue
                if response.status_code != 200:
                    raise error(f"{label} вернул HTTP {response.status_code}")
                async for chunk in response.aiter_bytes():
                    total += len(chunk)
                    if total > limit:
                        raise error(f"ответ больше лимита {limit >> 20} МБ")
                    chunks.append(chunk)
        except httpx.HTTPError as exc:
            raise error(f"{label} недоступен: {exc}") from exc
        break
    else:
        raise error(f"{label}: слишком много перенаправлений")
    try:
        return b"".join(chunks).decode("utf-8-sig")
    except UnicodeDecodeError as exc:
        raise error(f"{label}: схема выгрузки изменилась — ответ не в UTF-8") from exc


def check_list_floors(total: int, matchable: int, source: DumpSource) -> None:
    """A downloaded list with fewer entries than `source.min_total`, or fewer matchable
    (ИНН-bearing) ones than `source.min_matchable`, is truncated or has lost its identifier:
    loading it would turn every lookup into a false "not listed"."""
    if total < source.min_total or matchable < source.min_matchable:
        raise source.error(
            f"{source.label}: схема ответа изменилась — {total} записей, из них {matchable} с ИНН"
        )


def as_aware(value: datetime.datetime) -> datetime.datetime:
    """SQLite hands `DateTime(timezone=True)` back naive; the value was written as UTC."""
    return value if value.tzinfo else value.replace(tzinfo=datetime.UTC)


async def replace_dump(
    db: AsyncSession,
    source: DumpSource,
    records: list[dict],
    *,
    dump_date: datetime.date,
    valid_until: datetime.date | None,
    url: str,
) -> RegistryDump:
    """Replace `source.model`'s rows with `records` and record provenance, in the caller's
    transaction. Refuses (old data untouched) an empty version or one smaller than
    `MIN_ROW_RATIO` of the loaded one. Must run under `refresh_lock(source.key)` (enforced -
    a programming error, so a `RuntimeError`, not the source's error class)."""
    if not refresh_lock(source.key).locked():
        raise RuntimeError(f"replace_dump({source.key!r}) called without holding its refresh_lock")
    previous = await db.get(RegistryDump, source.key)
    previous_count = previous.row_count if previous else 0
    if not records or len(records) < previous_count * MIN_ROW_RATIO:
        raise source.error(
            f"{source.label}: схема выгрузки изменилась — {len(records)} записей вместо "
            f"~{previous_count}"
        )

    await db.execute(delete(source.model))
    for start in range(0, len(records), INSERT_CHUNK):
        await db.execute(insert(source.model), records[start : start + INSERT_CHUNK])

    now = datetime.datetime.now(datetime.UTC)
    if previous is None:
        previous = RegistryDump(source=source.key)
        db.add(previous)
    previous.dump_date = dump_date
    previous.valid_until = valid_until
    previous.row_count = len(records)
    previous.url = url
    previous.refreshed_at = now
    await db.flush()
    return previous


async def is_stale(db: AsyncSession, source: str, max_age: datetime.timedelta) -> bool:
    """No dump loaded, or not refreshed within `max_age` - re-derived from the DB so a
    process that restarts more often than the job's in-memory countdown still catches up
    (see the scheduler convention in AGENTS.md)."""
    meta = await db.get(RegistryDump, source)
    if meta is None:
        return True
    return datetime.datetime.now(datetime.UTC) - as_aware(meta.refreshed_at) > max_age


async def refresh_published_list(
    db: AsyncSession,
    source: DumpSource,
    *,
    url: str,
    parse: Callable[[str], tuple[list[dict], int]],
) -> dict:
    """Download a list published as one live file (no version date), parse it into
    `(records, total entries)`, check the sanity floors and replace the local copy - the
    whole refresh of the ЦБ and OFAC lists, which differ only in parser, URL and redirects."""
    async with dump_client() as client:
        text = await download_text(client, url, source)
    records, total = parse(text)
    check_list_floors(total, len(records), source)
    await replace_dump(
        db,
        source,
        records,
        dump_date=datetime.datetime.now(datetime.UTC).date(),
        valid_until=None,
        url=url,
    )
    return {"entries": total, "with_inn": len(records), "url": url}


async def loaded_meta(db: AsyncSession, source: DumpSource, *, not_loaded: str) -> RegistryDump:
    """The dump's provenance row; `source.error(not_loaded)` when it was never downloaded, so
    a lookup against an empty table reports "not checked", never "not listed"."""
    meta = await db.get(RegistryDump, source.key)
    if meta is None:
        raise source.error(not_loaded)
    return meta


def freshness(meta: RegistryDump, outdated_after: datetime.timedelta) -> dict:
    """`{as_of, outdated}` for a lookup result: the local copy's date, and whether it is
    older than the publisher's own update rhythm allows."""
    refreshed = as_aware(meta.refreshed_at)
    return {
        "as_of": refreshed.date().isoformat(),
        "outdated": datetime.datetime.now(datetime.UTC) - refreshed > outdated_after,
    }
