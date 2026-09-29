"""HTTP-level coverage for sanctions_search_routes.py: status codes and error mapping.
Matching logic itself is covered in test_sanctions_search_service.py."""

import contextlib
import datetime
from collections.abc import AsyncGenerator

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_read_db
from app.core.exceptions import register_exception_handlers
from app.core.models.registry_dump import RegistryDump
from app.features.sanctions_search.models.sanctions_search_models import SanctionsEntry
from app.features.sanctions_search.routers import sanctions_search_routes
from app.features.sanctions_search.service import sanctions_search_service as svc
from app.features.sanctions_search.service import search_index as idx
from tests.conftest import run


@pytest.fixture
def session_factory(make_session_factory):
    return make_session_factory([SanctionsEntry.__table__, RegistryDump.__table__])


@pytest.fixture(autouse=True)
def _patch_index_session(monkeypatch, session_factory):
    @contextlib.asynccontextmanager
    async def fake_managed_session():
        async with session_factory() as db:
            yield db

    monkeypatch.setattr(idx, "managed_session", fake_managed_session)
    idx.invalidate_index()
    yield
    idx.invalidate_index()


@pytest.fixture
def client(session_factory):
    async def _get_read_db() -> AsyncGenerator[AsyncSession]:
        async with session_factory() as db:
            yield db

    app = FastAPI()
    register_exception_handlers(app)
    app.include_router(sanctions_search_routes.router)
    app.dependency_overrides[get_read_db] = _get_read_db
    return TestClient(app)


def _seed_loaded(session_factory, entries):
    async def _go():
        async with session_factory() as db:
            for e in entries:
                db.add(SanctionsEntry(**e))
            db.add(
                RegistryDump(
                    source=svc.SOURCE_KEY,
                    dump_date=datetime.date(2026, 9, 29),
                    valid_until=None,
                    row_count=len(entries),
                    url=svc.LIST_URL,
                    refreshed_at=datetime.datetime.now(datetime.UTC),
                )
            )
            await db.commit()

    run(_go())


def _entry(**overrides):
    base = {
        "opensanctions_id": "NK-1",
        "schema": "Person",
        "name": "Jane Doe",
        "aliases": [],
        "countries": ["us"],
        "programs": [],
        "sanctions": None,
        "first_seen": None,
        "last_seen": None,
    }
    base.update(overrides)
    return base


def test_search_returns_matches(client, session_factory):
    _seed_loaded(session_factory, [_entry()])
    response = client.get("/api/sanctions-search/search", params={"q": "Jane Doe"})
    assert response.status_code == 200
    body = response.json()
    assert body["total_matches"] == 1
    assert body["matches"][0]["opensanctions_id"] == "NK-1"
    assert body["outdated"] is False


def test_search_503s_when_the_list_was_never_loaded(client, session_factory):
    response = client.get("/api/sanctions-search/search", params={"q": "anything"})
    assert response.status_code == 503
    assert response.json()["error_code"] == "sanctions_list_not_loaded"


def test_search_422s_below_the_minimum_query_length(client, session_factory):
    _seed_loaded(session_factory, [_entry()])
    response = client.get("/api/sanctions-search/search", params={"q": "ab"})
    assert response.status_code == 422


def test_schemas_lists_the_distinct_schemas_in_the_index(client, session_factory):
    _seed_loaded(
        session_factory,
        [
            _entry(opensanctions_id="NK-1", schema="Person"),
            _entry(opensanctions_id="NK-2", schema="Vessel"),
        ],
    )
    response = client.get("/api/sanctions-search/schemas")
    assert response.status_code == 200
    assert response.json() == ["Person", "Vessel"]
