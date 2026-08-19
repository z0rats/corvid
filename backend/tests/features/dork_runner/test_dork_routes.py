import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from app.core.config.rate_limit_config import limiter
from app.features.dork_runner.routers import dork_routes
from app.features.dork_runner.schemas.dork_schemas import DorkRunResponse


@pytest.fixture
def client():
    app = FastAPI()
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
    app.include_router(dork_routes.router)
    return TestClient(app)


class TestRunDorkScan:
    def test_delegates_to_perform_dork_run_and_returns_its_response(self, client, monkeypatch):
        async def fake_perform_dork_run(request):
            assert request.target == "example.com"
            return DorkRunResponse(
                target="example.com",
                target_type="domain",
                engine="duckduckgo",
                results=[],
                total_results=0,
                queries_run=3,
                errors=[],
            )

        monkeypatch.setattr(dork_routes, "perform_dork_run", fake_perform_dork_run)

        response = client.post(
            "/api/dork-runner/run", json={"target": "example.com", "target_type": "domain"}
        )

        assert response.status_code == 200
        assert response.json()["queries_run"] == 3

    def test_rejects_a_request_with_no_target(self, client):
        response = client.post("/api/dork-runner/run", json={"target_type": "domain"})

        assert response.status_code == 422

    def test_rejects_an_invalid_target_type(self, client):
        response = client.post(
            "/api/dork-runner/run", json={"target": "example.com", "target_type": "not-a-type"}
        )

        assert response.status_code == 422


class TestListDorkTemplates:
    def test_returns_only_templates_applicable_to_the_target_type(self, client):
        response = client.get("/api/dork-runner/templates", params={"target_type": "username"})

        assert response.status_code == 200
        body = response.json()
        assert len(body) > 0
        assert all("username" in t["target_types"] for t in body)

    def test_requires_the_target_type_query_param(self, client):
        response = client.get("/api/dork-runner/templates")

        assert response.status_code == 422
