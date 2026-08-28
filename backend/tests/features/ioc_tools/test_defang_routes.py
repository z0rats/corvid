from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.features.ioc_tools.ioc_defanger.routers import internal_defang_routes


def _client():
    app = FastAPI()
    app.include_router(internal_defang_routes.router)
    return TestClient(app)


class TestProcessIocs:
    def test_defangs_the_submitted_text(self):
        response = _client().post("/api/defang/", json={"text": "1.2.3.4", "operation": "defang"})

        assert response.status_code == 200
        body = response.json()
        assert body["results"][0]["processed"] == "1[.]2[.]3[.]4"
        assert body["total_processed"] == 1

    def test_fangs_the_submitted_text(self):
        response = _client().post(
            "/api/defang/", json={"text": "1[.]2[.]3[.]4", "operation": "fang"}
        )

        assert response.status_code == 200
        assert response.json()["results"][0]["processed"] == "1.2.3.4"

    def test_defaults_to_defang_when_operation_is_omitted(self):
        response = _client().post("/api/defang/", json={"text": "1.2.3.4"})

        assert response.status_code == 200
        assert response.json()["results"][0]["processed"] == "1[.]2[.]3[.]4"

    def test_rejects_an_invalid_operation_with_400(self):
        response = _client().post("/api/defang/", json={"text": "1.2.3.4", "operation": "delete"})

        # "operation" is a constrained enum field, so an out-of-set value never
        # reaches the route handler's own ValueError->400 mapping - pydantic
        # rejects it at the request-validation layer first.
        assert response.status_code == 422

    def test_rejects_missing_text_with_422(self):
        response = _client().post("/api/defang/", json={"operation": "defang"})

        assert response.status_code == 422

    def test_rejects_whitespace_only_text_with_422(self):
        response = _client().post("/api/defang/", json={"text": "   "})

        assert response.status_code == 422
