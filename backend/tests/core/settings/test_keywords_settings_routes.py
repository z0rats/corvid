from collections.abc import AsyncGenerator

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_db, get_read_db
from app.core.exceptions import register_exception_handlers
from app.core.settings.keywords.models.keywords_settings_models import Keyword
from app.core.settings.keywords.routers.keywords_settings_routes import router


@pytest.fixture
def client(make_session_factory):
    session_factory = make_session_factory([Keyword.__table__])

    async def _get_db() -> AsyncGenerator[AsyncSession]:
        async with session_factory() as db:
            yield db
            await db.commit()

    app = FastAPI()
    register_exception_handlers(app)
    app.include_router(router)
    app.dependency_overrides[get_db] = _get_db
    app.dependency_overrides[get_read_db] = _get_db
    return TestClient(app)


class TestListKeywords:
    def test_returns_an_empty_list_initially(self, client):
        response = client.get("/api/settings/keywords")
        assert response.status_code == 200
        assert response.json() == []

    def test_returns_created_keywords(self, client):
        client.post("/api/settings/keywords", json={"keyword": "malware"})

        response = client.get("/api/settings/keywords")

        assert response.status_code == 200
        assert response.json()[0]["keyword"] == "malware"

    def test_respects_the_limit_query_param(self, client):
        for value in ["alpha", "beta", "gamma"]:
            client.post("/api/settings/keywords", json={"keyword": value})

        response = client.get("/api/settings/keywords", params={"limit": 1})

        assert response.status_code == 200
        assert len(response.json()) == 1


class TestGetKeyword:
    def test_returns_404_for_a_missing_id(self, client):
        response = client.get("/api/settings/keywords/999")
        assert response.status_code == 404

    def test_returns_the_matching_keyword(self, client):
        created = client.post("/api/settings/keywords", json={"keyword": "phishing"}).json()

        response = client.get(f"/api/settings/keywords/{created['id']}")

        assert response.status_code == 200
        assert response.json()["keyword"] == "phishing"


class TestCreateKeyword:
    def test_creates_and_normalizes_the_keyword(self, client):
        response = client.post("/api/settings/keywords", json={"keyword": "  Malware  "})

        assert response.status_code == 201
        assert response.json()["keyword"] == "malware"

    def test_rejects_disallowed_characters_at_the_schema_layer(self, client):
        response = client.post("/api/settings/keywords", json={"keyword": "mal;ware"})
        assert response.status_code == 422

    def test_rejects_a_duplicate_keyword(self, client):
        client.post("/api/settings/keywords", json={"keyword": "malware"})

        response = client.post("/api/settings/keywords", json={"keyword": "MALWARE"})

        assert response.status_code == 400


class TestUpdateKeyword:
    def test_updates_the_keyword_value(self, client):
        created = client.post("/api/settings/keywords", json={"keyword": "old"}).json()

        response = client.put(f"/api/settings/keywords/{created['id']}", json={"keyword": "new"})

        assert response.status_code == 200
        assert response.json()["keyword"] == "new"

    def test_returns_404_for_a_missing_id(self, client):
        response = client.put("/api/settings/keywords/999", json={"keyword": "new"})
        assert response.status_code == 404


class TestDeleteKeyword:
    def test_deletes_an_existing_keyword(self, client):
        created = client.post("/api/settings/keywords", json={"keyword": "gone"}).json()

        response = client.delete(f"/api/settings/keywords/{created['id']}")

        assert response.status_code == 200
        assert response.json()["detail"] == "Keyword deleted successfully"
        assert client.get(f"/api/settings/keywords/{created['id']}").status_code == 404

    def test_returns_404_for_a_missing_id(self, client):
        response = client.delete("/api/settings/keywords/999")
        assert response.status_code == 404
