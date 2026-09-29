"""Resolves Steam's numeric location codes to names via the keyless
`steamcommunity.com/actions/QueryLocations` endpoint (fixed host, undocumented).

Best-effort by design: a profile summary carries only `loccountrycode`/`locstatecode`/
`loccityid`, and a failed or empty lookup just leaves the names out - the codes still render.
Results are cached in-process, with one lock per cache key so concurrent lookups (a scan
resolving hundreds of friends) share a single fetch instead of each racing to the network.
"""

import asyncio
import logging
import time
from typing import Any

import httpx

logger = logging.getLogger(__name__)

QUERY_LOCATIONS_URL = "https://steamcommunity.com/actions/QueryLocations"
QUERY_LOCATIONS_TIMEOUT = 10.0
CACHE_TTL_SECONDS = 24 * 3600

_cache: dict[str, tuple[float, list[dict[str, Any]]]] = {}
_locks: dict[str, asyncio.Lock] = {}


async def _query(path: str) -> list[dict[str, Any]]:
    """Cached list for `QueryLocations/<path>`; [] on any failure or a `null` body."""
    lock = _locks.setdefault(path, asyncio.Lock())
    async with lock:
        cached = _cache.get(path)
        if cached and cached[0] > time.monotonic():
            return cached[1]

        try:
            async with httpx.AsyncClient(timeout=QUERY_LOCATIONS_TIMEOUT) as client:
                response = await client.get(f"{QUERY_LOCATIONS_URL}/{path}".rstrip("/"))
            if response.status_code != 200:
                return []
            data = response.json()
        except (httpx.HTTPError, ValueError) as exc:
            logger.warning("Steam QueryLocations/%s failed: %s", path, type(exc).__name__)
            return []

        entries = [e for e in data if isinstance(e, dict)] if isinstance(data, list) else []
        _cache[path] = (time.monotonic() + CACHE_TTL_SECONDS, entries)
        return entries


async def resolve_location_names(
    country_code: str | None, state_code: str | None, city_id: int | None
) -> dict[str, str | None]:
    """Human-readable `country`/`state`/`city` names for Steam's location codes (each None if
    unresolved). A city needs both a country and a state code to be looked up."""
    names: dict[str, str | None] = {"country": None, "state": None, "city": None}
    if not country_code:
        return names

    for country in await _query(""):
        if country.get("countrycode") == country_code:
            names["country"] = country.get("countryname")
            break

    if state_code:
        for state in await _query(country_code):
            if state.get("statecode") == state_code:
                names["state"] = state.get("statename")
                break

        if city_id is not None:
            for city in await _query(f"{country_code}/{state_code}"):
                if city.get("cityid") == city_id:
                    names["city"] = city.get("cityname")
                    break
    return names
