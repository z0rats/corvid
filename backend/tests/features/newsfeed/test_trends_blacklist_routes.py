import asyncio
from collections.abc import AsyncGenerator

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_db, get_read_db
from app.core.exceptions import register_exception_handlers
from app.features.newsfeed.models.newsfeed_models import TrendsBlacklistEntry
from app.features.newsfeed.routers import trends_blacklist_routes


@pytest.fixture
def session_factory(make_session_factory):
    return make_session_factory([TrendsBlacklistEntry.__table__])


@pytest.fixture
def client(session_factory):
    async def _get_db() -> AsyncGenerator[AsyncSession]:
        async with session_factory() as db:
            yield db
            await db.commit()

    app = FastAPI()
    register_exception_handlers(app)
    app.include_router(trends_blacklist_routes.router)
    app.dependency_overrides[get_db] = _get_db
    app.dependency_overrides[get_read_db] = _get_db
    return TestClient(app)


def _seed_entry(session_factory, value: str, entry_type: str) -> int:
    async def _seed():
        async with session_factory() as db:
            entry = TrendsBlacklistEntry(value=value, type=entry_type)
            db.add(entry)
            await db.commit()
            return entry.id

    return asyncio.run(_seed())


class TestListBlacklistEntries:
    def test_returns_an_empty_list_initially(self, client):
        response = client.get("/api/settings/newsfeed/trends-blacklist")
        assert response.status_code == 200
        assert response.json() == []

    def test_returns_all_entries_when_unfiltered(self, client, session_factory):
        _seed_entry(session_factory, "malware", "word")
        _seed_entry(session_factory, "1.2.3.4", "ioc")

        response = client.get("/api/settings/newsfeed/trends-blacklist")

        assert response.status_code == 200
        assert {e["value"] for e in response.json()} == {"malware", "1.2.3.4"}

    def test_filters_by_type(self, client, session_factory):
        _seed_entry(session_factory, "malware", "word")
        _seed_entry(session_factory, "1.2.3.4", "ioc")

        response = client.get("/api/settings/newsfeed/trends-blacklist", params={"type": "ioc"})

        assert response.status_code == 200
        body = response.json()
        assert len(body) == 1
        assert body[0]["value"] == "1.2.3.4"


class TestAddBlacklistEntry:
    def test_creates_a_new_entry_and_normalizes_it(self, client):
        response = client.post(
            "/api/settings/newsfeed/trends-blacklist",
            json={"value": "  Malware  ", "type": "word"},
        )

        assert response.status_code == 201
        body = response.json()
        assert body["value"] == "malware"
        assert body["type"] == "word"

    def test_rejects_a_duplicate_entry_of_the_same_type(self, client):
        client.post(
            "/api/settings/newsfeed/trends-blacklist", json={"value": "malware", "type": "word"}
        )

        response = client.post(
            "/api/settings/newsfeed/trends-blacklist", json={"value": "MALWARE", "type": "word"}
        )

        assert response.status_code == 400
        assert response.json()["error_code"] == "BLACKLIST_ENTRY_EXISTS"

    def test_the_same_value_is_allowed_for_a_different_type(self, client):
        client.post(
            "/api/settings/newsfeed/trends-blacklist", json={"value": "phish", "type": "word"}
        )

        response = client.post(
            "/api/settings/newsfeed/trends-blacklist", json={"value": "phish", "type": "ioc"}
        )

        assert response.status_code == 201

    def test_rejects_an_invalid_type(self, client):
        response = client.post(
            "/api/settings/newsfeed/trends-blacklist", json={"value": "x", "type": "url"}
        )
        assert response.status_code == 422

    def test_rejects_an_empty_value(self, client):
        response = client.post(
            "/api/settings/newsfeed/trends-blacklist", json={"value": "", "type": "word"}
        )
        assert response.status_code == 422


class TestRemoveBlacklistEntry:
    def test_returns_404_for_an_unknown_id(self, client):
        response = client.delete("/api/settings/newsfeed/trends-blacklist/999")
        assert response.status_code == 404
        assert response.json()["error_code"] == "BLACKLIST_ENTRY_NOT_FOUND"

    def test_deletes_an_existing_entry(self, client, session_factory):
        entry_id = _seed_entry(session_factory, "malware", "word")

        response = client.delete(f"/api/settings/newsfeed/trends-blacklist/{entry_id}")

        assert response.status_code == 200
        assert response.json()["detail"] == "Blacklist entry deleted successfully"

        follow_up = client.get("/api/settings/newsfeed/trends-blacklist")
        assert follow_up.json() == []
