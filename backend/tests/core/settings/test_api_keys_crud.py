import asyncio

import pytest
from cryptography.fernet import Fernet
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

from app.core.database import Base
from app.core.security import secrets_crypto
from app.core.settings.api_keys.crud.api_keys_settings_crud import (
    create_new_apikey,
    delete_existing_apikey,
    get_apikey,
    get_apikeys,
    upsert_apikey_bulk_lookup,
)
from app.core.settings.api_keys.models.api_keys_settings_models import Apikey
from app.core.settings.api_keys.schemas.api_keys_settings_schemas import ApikeyCreateRequest


def _run(coro):
    return asyncio.run(coro)


@pytest.fixture
def engine():
    return create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )


@pytest.fixture
def session_factory(engine):
    async def _create_tables():
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all, tables=[Apikey.__table__])

    _run(_create_tables())
    return async_sessionmaker(engine, expire_on_commit=False)


@pytest.fixture(autouse=True)
def fixed_fernet(monkeypatch):
    fixed = Fernet(Fernet.generate_key())
    monkeypatch.setattr(secrets_crypto, "_get_fernet", lambda: fixed)


class TestCreateNewApikey:
    def test_creates_row_from_request(self, session_factory):
        async def _scenario():
            async with session_factory() as db:
                created = await create_new_apikey(
                    db,
                    ApikeyCreateRequest(name="virustotal", key="abc123"),
                )
                await db.commit()
                return created

        created = _run(_scenario())
        assert created.name == "virustotal"
        assert created.key == "abc123"
        assert created.is_active is False


class TestGetApikeys:
    def test_returns_empty_list_when_none_exist(self, session_factory):
        async def _scenario():
            async with session_factory() as db:
                return await get_apikeys(db)

        assert _run(_scenario()) == []

    def test_returns_all_created_keys(self, session_factory):
        async def _scenario():
            async with session_factory() as db:
                await create_new_apikey(db, ApikeyCreateRequest(name="virustotal", key="a"))
                await create_new_apikey(db, ApikeyCreateRequest(name="shodan", key="b"))
                await db.commit()
            async with session_factory() as db:
                return await get_apikeys(db)

        keys = _run(_scenario())
        assert {k.name for k in keys} == {"virustotal", "shodan"}

    def test_respects_skip_and_limit(self, session_factory):
        async def _scenario():
            async with session_factory() as db:
                for name in ["a", "b", "c"]:
                    await create_new_apikey(db, ApikeyCreateRequest(name=name, key="k"))
                await db.commit()
            async with session_factory() as db:
                return await get_apikeys(db, skip=1, limit=1)

        keys = _run(_scenario())
        assert len(keys) == 1


class TestGetApikey:
    def test_returns_none_when_missing(self, session_factory):
        async def _scenario():
            async with session_factory() as db:
                return await get_apikey(db, "nonexistent")

        assert _run(_scenario()) is None

    def test_returns_matching_key(self, session_factory):
        async def _scenario():
            async with session_factory() as db:
                await create_new_apikey(db, ApikeyCreateRequest(name="virustotal", key="abc"))
                await db.commit()
            async with session_factory() as db:
                return await get_apikey(db, "virustotal")

        found = _run(_scenario())
        assert found is not None
        assert found.key == "abc"


class TestUpsertApikeyBulkLookup:
    def test_updates_flag_on_existing_key(self, session_factory):
        async def _scenario():
            async with session_factory() as db:
                await create_new_apikey(db, ApikeyCreateRequest(name="virustotal", key="abc"))
                await db.commit()
            async with session_factory() as db:
                result = await upsert_apikey_bulk_lookup(db, "virustotal", True)
                await db.commit()
                return result

        result = _run(_scenario())
        assert result.bulk_ioc_lookup is True
        assert result.key == "abc"

    def test_creates_minimal_record_when_key_does_not_exist(self, session_factory):
        async def _scenario():
            async with session_factory() as db:
                result = await upsert_apikey_bulk_lookup(db, "shodan", True)
                await db.commit()
                return result

        result = _run(_scenario())
        assert result.name == "shodan"
        assert result.key == ""
        assert result.is_active is False
        assert result.bulk_ioc_lookup is True


class TestDeleteExistingApikey:
    def test_deletes_existing_key_and_returns_true(self, session_factory):
        async def _scenario():
            async with session_factory() as db:
                await create_new_apikey(db, ApikeyCreateRequest(name="virustotal", key="abc"))
                await db.commit()
            async with session_factory() as db:
                deleted = await delete_existing_apikey(db, "virustotal")
                await db.commit()
                return deleted

        assert _run(_scenario()) is True

        async def _verify():
            async with session_factory() as db:
                return await get_apikey(db, "virustotal")

        assert _run(_verify()) is None

    def test_returns_false_when_key_does_not_exist(self, session_factory):
        async def _scenario():
            async with session_factory() as db:
                return await delete_existing_apikey(db, "nonexistent")

        assert _run(_scenario()) is False
