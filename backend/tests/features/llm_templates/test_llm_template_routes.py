from collections.abc import AsyncGenerator

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config.rate_limit_config import limiter
from app.core.dependencies import get_db, get_read_db
from app.core.exceptions import register_exception_handlers
from app.features.llm_templates.models.llm_template_models import AITemplate
from app.features.llm_templates.models.template_category_models import TemplateCategory
from app.features.llm_templates.routers import llm_template_routes


@pytest.fixture
def client(make_session_factory):
    session_factory = make_session_factory([TemplateCategory.__table__, AITemplate.__table__])

    async def _get_db() -> AsyncGenerator[AsyncSession]:
        async with session_factory() as db:
            yield db
            await db.commit()

    app = FastAPI()
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
    register_exception_handlers(app)
    app.include_router(llm_template_routes.router)
    app.dependency_overrides[get_db] = _get_db
    app.dependency_overrides[get_read_db] = _get_db
    return TestClient(app, raise_server_exceptions=False)


def _template_payload(**overrides):
    defaults = {"title": "Test Template", "ai_agent_role": "role", "ai_agent_task": "task"}
    return {**defaults, **overrides}


class TestCreateAndGetTemplate:
    def test_creates_a_template_and_returns_it(self, client):
        response = client.post("/api/ai-templates", json=_template_payload())

        assert response.status_code == 201
        body = response.json()
        assert body["title"] == "Test Template"
        assert body["id"]

    def test_get_by_id_returns_404_for_an_unknown_id(self, client):
        response = client.get("/api/ai-templates/does-not-exist")

        assert response.status_code == 404
        assert response.json()["error_code"] == "TEMPLATE_NOT_FOUND"

    def test_get_by_id_returns_a_created_template(self, client):
        created = client.post("/api/ai-templates", json=_template_payload()).json()

        response = client.get(f"/api/ai-templates/{created['id']}")

        assert response.status_code == 200
        assert response.json()["id"] == created["id"]

    def test_create_rejects_a_duplicate_payload_field_name(self, client):
        # Regression test for a core/exceptions.py bug (not llm_templates-specific):
        # pydantic v2 embeds the raw exception instance under errors()[i]['ctx']
        # ['error'] for any field_validator that raises a bare ValueError (the
        # idiomatic pattern this exact validator uses) - that isn't JSON-serializable,
        # so this 422 used to crash into a 500 in dev/test instead of reporting the
        # validation failure. See _stringify_ctx_error in core/exceptions.py.
        response = client.post(
            "/api/ai-templates",
            json=_template_payload(
                payload_fields=[
                    {"name": "x", "description": "d1"},
                    {"name": "x", "description": "d2"},
                ]
            ),
        )

        assert response.status_code == 422
        assert "Duplicate payload field name" in response.text


class TestListTemplates:
    def test_returns_created_templates_ordered_by_order_number(self, client):
        client.post("/api/ai-templates", json=_template_payload(title="Second", order_number=20))
        client.post("/api/ai-templates", json=_template_payload(title="First", order_number=10))

        response = client.get("/api/ai-templates")

        assert response.status_code == 200
        titles = [t["title"] for t in response.json()]
        assert titles == ["First", "Second"]


class TestUpdateTemplate:
    def test_returns_404_for_an_unknown_id(self, client):
        response = client.put("/api/ai-templates/does-not-exist", json={"title": "new"})

        assert response.status_code == 404

    def test_updates_an_existing_template(self, client):
        created = client.post("/api/ai-templates", json=_template_payload()).json()

        response = client.put(f"/api/ai-templates/{created['id']}", json={"title": "Renamed"})

        assert response.status_code == 200
        assert response.json()["title"] == "Renamed"


class TestDeleteTemplate:
    def test_returns_404_for_an_unknown_id(self, client):
        response = client.delete("/api/ai-templates/does-not-exist")

        assert response.status_code == 404

    def test_deletes_an_existing_template(self, client):
        created = client.post("/api/ai-templates", json=_template_payload()).json()

        response = client.delete(f"/api/ai-templates/{created['id']}")
        assert response.status_code == 200

        follow_up = client.get(f"/api/ai-templates/{created['id']}")
        assert follow_up.status_code == 404


class TestReorderTemplates:
    def test_reorders_and_reports_the_updated_count(self, client):
        first = client.post("/api/ai-templates", json=_template_payload(title="A")).json()
        second = client.post("/api/ai-templates", json=_template_payload(title="B")).json()

        response = client.post(
            "/api/ai-templates/reorder", json={"template_ids": [second["id"], first["id"]]}
        )

        assert response.status_code == 200
        assert response.json()["updated_count"] == 2


class TestEngineerPrompt:
    def test_returns_the_engineered_prompt_on_success(self, client, monkeypatch):
        async def fake_run_engineer_prompt(title, description, model_id, db):
            return {
                "ai_agent_role": "role",
                "ai_agent_task": "task",
                "payload_fields": [],
                "example_input_output": "example",
            }

        monkeypatch.setattr(llm_template_routes, "run_engineer_prompt", fake_run_engineer_prompt)

        response = client.post(
            "/api/ai-templates/prompt-engineer", json={"title": "T", "description": "D"}
        )

        assert response.status_code == 200
        assert response.json()["ai_agent_role"] == "role"

    def test_maps_a_value_error_from_the_service_to_a_422(self, client, monkeypatch):
        async def failing_run_engineer_prompt(title, description, model_id, db):
            raise ValueError("no models configured")

        monkeypatch.setattr(llm_template_routes, "run_engineer_prompt", failing_run_engineer_prompt)

        response = client.post(
            "/api/ai-templates/prompt-engineer", json={"title": "T", "description": "D"}
        )

        assert response.status_code == 422
        assert response.json()["error_code"] == "TEMPLATE_ENGINEER_FAILED"


class TestExecuteTemplate:
    def test_returns_404_when_the_template_does_not_exist(self, client):
        response = client.post(
            "/api/ai-templates/execute/does-not-exist",
            json={"template_id": "x", "payload_data": {}},
        )

        assert response.status_code == 404

    def test_returns_the_llm_result_on_success(self, client, monkeypatch):
        created = client.post("/api/ai-templates", json=_template_payload()).json()

        async def fake_run_execute_template(template, execution_data, db):
            return "the llm result"

        monkeypatch.setattr(llm_template_routes, "run_execute_template", fake_run_execute_template)

        response = client.post(
            f"/api/ai-templates/execute/{created['id']}",
            json={"template_id": created["id"], "payload_data": {}},
        )

        assert response.status_code == 200
        assert response.json()["result"] == "the llm result"

    def test_maps_a_value_error_from_the_service_to_a_422(self, client, monkeypatch):
        created = client.post("/api/ai-templates", json=_template_payload()).json()

        async def failing_run_execute_template(template, execution_data, db):
            raise ValueError("missing required payload fields: logs")

        monkeypatch.setattr(
            llm_template_routes, "run_execute_template", failing_run_execute_template
        )

        response = client.post(
            f"/api/ai-templates/execute/{created['id']}",
            json={"template_id": created["id"], "payload_data": {}},
        )

        assert response.status_code == 422
        assert response.json()["error_code"] == "TEMPLATE_EXECUTE_FAILED"
