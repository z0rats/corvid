import asyncio
from collections.abc import AsyncGenerator

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_db, get_read_db
from app.core.exceptions import register_exception_handlers
from app.features.llm_templates.constants import DEFAULT_CATEGORY_ID
from app.features.llm_templates.crud.template_category_crud import ensure_system_categories_exist
from app.features.llm_templates.models.llm_template_models import AITemplate
from app.features.llm_templates.models.template_category_models import TemplateCategory
from app.features.llm_templates.routers import llm_template_routes, template_category_routes


def _run(coro):
    return asyncio.run(coro)


@pytest.fixture
def session_factory(make_session_factory):
    return make_session_factory([TemplateCategory.__table__, AITemplate.__table__])


@pytest.fixture
def client(session_factory):
    async def _get_db() -> AsyncGenerator[AsyncSession]:
        async with session_factory() as db:
            yield db
            await db.commit()

    app = FastAPI()
    register_exception_handlers(app)
    app.include_router(template_category_routes.router)
    app.include_router(llm_template_routes.router)
    app.dependency_overrides[get_db] = _get_db
    app.dependency_overrides[get_read_db] = _get_db
    return TestClient(app)


def _seed_system_categories(session_factory):
    async def _scenario():
        async with session_factory() as db:
            await ensure_system_categories_exist(db)
            await db.commit()

    _run(_scenario())


class TestListAndCreateCategory:
    def test_creates_a_category_and_returns_it(self, client):
        response = client.post("/api/ai-templates/groups", json={"name": "My Group"})

        assert response.status_code == 201
        body = response.json()
        assert body["name"] == "My Group"
        assert body["is_system"] is False

    def test_lists_created_categories(self, client):
        client.post("/api/ai-templates/groups", json={"name": "A"})
        client.post("/api/ai-templates/groups", json={"name": "B"})

        response = client.get("/api/ai-templates/groups")

        assert response.status_code == 200
        assert [c["name"] for c in response.json()] == ["A", "B"]


class TestRenameCategory:
    def test_returns_404_for_an_unknown_id(self, client):
        response = client.put("/api/ai-templates/groups/does-not-exist", json={"name": "new"})

        assert response.status_code == 404

    def test_renames_a_non_system_category(self, client):
        created = client.post("/api/ai-templates/groups", json={"name": "Old"}).json()

        response = client.put(f"/api/ai-templates/groups/{created['id']}", json={"name": "New"})

        assert response.status_code == 200
        assert response.json()["name"] == "New"

    def test_returns_400_for_a_system_category(self, client, session_factory):
        _seed_system_categories(session_factory)

        response = client.put(
            f"/api/ai-templates/groups/{DEFAULT_CATEGORY_ID}", json={"name": "Renamed"}
        )

        assert response.status_code == 400
        assert response.json()["error_code"] == "CATEGORY_RENAME_INVALID"


class TestDeleteCategory:
    def test_returns_404_for_an_unknown_id(self, client):
        response = client.request(
            "DELETE", "/api/ai-templates/groups/does-not-exist", json={"action": "move_to_default"}
        )

        assert response.status_code == 404

    def test_deletes_a_non_system_category(self, client):
        created = client.post("/api/ai-templates/groups", json={"name": "To Delete"}).json()

        response = client.request(
            "DELETE",
            f"/api/ai-templates/groups/{created['id']}",
            json={"action": "move_to_default"},
        )

        assert response.status_code == 200

    def test_returns_400_for_a_system_category(self, client, session_factory):
        _seed_system_categories(session_factory)

        response = client.request(
            "DELETE",
            f"/api/ai-templates/groups/{DEFAULT_CATEGORY_ID}",
            json={"action": "move_to_default"},
        )

        assert response.status_code == 400
        assert response.json()["error_code"] == "CATEGORY_DELETE_INVALID"


class TestReorderCategories:
    def test_reorders_and_reports_the_updated_count(self, client):
        a = client.post("/api/ai-templates/groups", json={"name": "A"}).json()
        b = client.post("/api/ai-templates/groups", json={"name": "B"}).json()

        response = client.post(
            "/api/ai-templates/groups/reorder", json={"category_ids": [b["id"], a["id"]]}
        )

        assert response.status_code == 200
        assert response.json()["updated_count"] == 2


class TestMoveTemplates:
    def test_moves_templates_and_reports_the_count(self, client):
        category = client.post("/api/ai-templates/groups", json={"name": "Target"}).json()
        template = client.post(
            "/api/ai-templates",
            json={"title": "t", "ai_agent_role": "r", "ai_agent_task": "k"},
        ).json()

        response = client.post(
            "/api/ai-templates/groups/move-templates",
            json={"template_ids": [template["id"]], "category_id": category["id"]},
        )

        assert response.status_code == 200
        assert "Moved 1" in response.json()["message"]
