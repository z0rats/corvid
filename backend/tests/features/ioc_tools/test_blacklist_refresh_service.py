"""Covers is_blacklist_stale (added after discovering the recurring blacklist_refresh
scheduler job can silently never fire: its in-memory APScheduler countdown resets on every
process restart, so on a host that restarts more often than the configured interval the
local blacklist can go stale indefinitely — is_blacklist_stale re-derives staleness from
the DB on every startup instead) and fetch_opensanctions_addresses' NDJSON parsing (filters
to CryptoWallet-schema entities, skips entities with no publicKey property)."""

import asyncio
import json
from datetime import UTC, datetime, timedelta

import httpx
import pytest
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

from app.core.database import Base
from app.features.ioc_tools.ioc_lookup.single_lookup.models.blacklist_models import (
    BlacklistedAddress,
    BlacklistSource,
)
from app.features.ioc_tools.ioc_lookup.single_lookup.service import blacklist_refresh_service
from app.features.ioc_tools.ioc_lookup.single_lookup.service.blacklist_refresh_service import (
    fetch_opensanctions_addresses,
    is_blacklist_stale,
)


def _run(coro):
    return asyncio.run(coro)


class _FakeClient:
    def __init__(self, response: httpx.Response):
        self._response = response

    async def get(self, url, **kwargs):
        return self._response


@pytest.fixture
def session_factory():
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    async def _create_tables():
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all, tables=[BlacklistedAddress.__table__])

    _run(_create_tables())
    return async_sessionmaker(engine, expire_on_commit=False)


class TestIsBlacklistStale:
    def test_empty_table_is_stale(self, session_factory):
        async def _scenario():
            async with session_factory() as db:
                return await is_blacklist_stale(db, timedelta(hours=24))

        assert _run(_scenario()) is True

    def test_recently_refreshed_row_is_not_stale(self, session_factory):
        async def _scenario():
            async with session_factory() as db:
                db.add(
                    BlacklistedAddress(
                        address="0xabc123",
                        source=BlacklistSource.OFAC.value,
                        last_seen_at=datetime.now(UTC) - timedelta(hours=1),
                    )
                )
                await db.commit()
                return await is_blacklist_stale(db, timedelta(hours=24))

        assert _run(_scenario()) is False

    def test_old_row_is_stale(self, session_factory):
        async def _scenario():
            async with session_factory() as db:
                db.add(
                    BlacklistedAddress(
                        address="0xabc123",
                        source=BlacklistSource.OFAC.value,
                        last_seen_at=datetime.now(UTC) - timedelta(hours=48),
                    )
                )
                await db.commit()
                return await is_blacklist_stale(db, timedelta(hours=24))

        assert _run(_scenario()) is True

    def test_not_stale_if_at_least_one_row_is_fresh(self, session_factory):
        async def _scenario():
            async with session_factory() as db:
                db.add(
                    BlacklistedAddress(
                        address="0xold",
                        source=BlacklistSource.OFAC.value,
                        last_seen_at=datetime.now(UTC) - timedelta(hours=48),
                    )
                )
                db.add(
                    BlacklistedAddress(
                        address="0xnew",
                        source=BlacklistSource.SCAMSNIFFER.value,
                        last_seen_at=datetime.now(UTC) - timedelta(hours=1),
                    )
                )
                await db.commit()
                return await is_blacklist_stale(db, timedelta(hours=24))

        assert _run(_scenario()) is False


_OPENSANCTIONS_NDJSON = "\n".join(
    [
        json.dumps(
            {
                "id": "il-1",
                "schema": "CryptoWallet",
                "properties": {
                    "publicKey": ["TWaertrZdpRJSbLv2G638UL5HCK6sKcZYy"],
                    "topics": ["crime.terror"],
                    "currency": ["USDT"],
                },
            }
        ),
        # References another entity in this same dump via `holder` - should resolve to its caption.
        json.dumps(
            {
                "id": "il-2",
                "schema": "CryptoWallet",
                "properties": {
                    "publicKey": ["0xE3740C1B2FcDA407027E2c80906306604E5260e7"],
                    "topics": ["crime.terror"],
                    "holder": ["il-nobitex"],
                },
            }
        ),
        json.dumps(
            {
                "id": "il-nobitex",
                "schema": "LegalEntity",
                "caption": "NOBITEX",
                "properties": {"name": ["NOBITEX"]},
            }
        ),
        # No publicKey (e.g. only a managingExchange/accountId pair) - not an address, skip.
        json.dumps(
            {
                "id": "il-3",
                "schema": "CryptoWallet",
                "properties": {"managingExchange": ["Binance"], "topics": ["crime.terror"]},
            }
        ),
        # Wrong schema (e.g. the Sanction/Person records also present in the dump) - skip.
        json.dumps({"id": "il-4", "schema": "Person", "properties": {"name": ["Someone"]}}),
        # Real il_mod_crypto data occasionally bakes a destination-tag annotation into the address
        # string itself - must be stripped or it would never match a clean lookup.
        json.dumps(
            {
                "id": "il-5",
                "schema": "CryptoWallet",
                "properties": {
                    "publicKey": ["rEb8TK3gBgk5auZkwc6sHnwrGVJH8DuaLh (Address tag 102334770)*"],
                    "topics": ["crime.terror"],
                },
            }
        ),
        "",  # blank line - skip.
    ]
)


class TestFetchOpensanctionsAddresses:
    def test_parses_only_cryptowallet_entities_with_a_public_key(self, monkeypatch):
        response = httpx.Response(
            200,
            request=httpx.Request("GET", "https://data.opensanctions.org/x"),
            content=_OPENSANCTIONS_NDJSON.encode(),
        )
        monkeypatch.setattr(blacklist_refresh_service, "get_client", lambda: _FakeClient(response))

        result = _run(fetch_opensanctions_addresses())

        assert result == [
            {
                "address": "TWaertrZdpRJSbLv2G638UL5HCK6sKcZYy",
                "chain": "USDT",
                "entity_name": None,
                "label": "crime.terror",
                "details": {
                    "dataset": "il_mod_crypto",
                    "profile_url": "https://www.opensanctions.org/entities/il-1/",
                },
            },
            {
                "address": "0xe3740c1b2fcda407027e2c80906306604e5260e7",
                "chain": None,
                "entity_name": "NOBITEX",
                "label": "crime.terror",
                "details": {
                    "dataset": "il_mod_crypto",
                    "profile_url": "https://www.opensanctions.org/entities/il-2/",
                },
            },
            {
                "address": "rEb8TK3gBgk5auZkwc6sHnwrGVJH8DuaLh",
                "chain": None,
                "entity_name": None,
                "label": "crime.terror",
                "details": {
                    "dataset": "il_mod_crypto",
                    "profile_url": "https://www.opensanctions.org/entities/il-5/",
                },
            },
        ]
