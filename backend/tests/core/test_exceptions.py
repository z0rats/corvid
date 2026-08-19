import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from pydantic import BaseModel, field_validator

from app.core.config.settings import settings
from app.core.exceptions import AppHTTPException, ApplicationError, register_exception_handlers


class _Model(BaseModel):
    name: str

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        if v == "bad":
            raise ValueError("name cannot be 'bad'")
        return v


@pytest.fixture
def client():
    app = FastAPI()
    register_exception_handlers(app)

    @app.post("/validated")
    def validated_endpoint(model: _Model):
        return {"ok": True}

    @app.get("/app-http-exception")
    def app_http_exception_endpoint():
        raise AppHTTPException(status_code=404, detail="not found", error_code="THING_NOT_FOUND")

    @app.get("/application-error")
    def application_error_endpoint():
        raise ApplicationError("business rule violated", status_code=409, error_code="CONFLICT")

    @app.get("/unhandled")
    def unhandled_endpoint():
        raise RuntimeError("something broke")

    return TestClient(app, raise_server_exceptions=False)


class TestValidationExceptionHandler:
    def test_a_field_validator_raising_a_bare_value_error_returns_a_clean_422(self, client):
        # Regression test: pydantic v2 embeds the raw ValueError instance under
        # errors()[i]['ctx']['error'] for this idiomatic field_validator pattern,
        # which isn't JSON-serializable - this used to crash the response itself
        # into a 500 instead of reporting the validation failure (dev/test only;
        # production's msg/type-only stripping happened to sidestep it).
        response = client.post("/validated", json={"name": "bad"})

        assert response.status_code == 422
        assert "cannot be 'bad'" in response.text

    def test_a_normal_type_validation_error_returns_a_clean_422(self, client):
        response = client.post("/validated", json={"name": 123})

        assert response.status_code == 422

    def test_sanitizes_to_msg_and_type_only_in_production(self, client, monkeypatch):
        monkeypatch.setattr(settings, "environment", "production")

        response = client.post("/validated", json={"name": "bad"})

        assert response.status_code == 422
        errors = response.json()["errors"]
        assert all(set(err.keys()) == {"msg", "type"} for err in errors)


class TestAppHttpExceptionHandler:
    def test_returns_the_status_code_and_error_code(self, client):
        response = client.get("/app-http-exception")

        assert response.status_code == 404
        assert response.json() == {"detail": "not found", "error_code": "THING_NOT_FOUND"}


class TestApplicationErrorHandler:
    def test_returns_the_configured_status_code_and_error_code(self, client):
        response = client.get("/application-error")

        assert response.status_code == 409
        assert response.json() == {"detail": "business rule violated", "error_code": "CONFLICT"}

    def test_rejects_a_status_code_outside_the_4xx_5xx_range(self):
        with pytest.raises(ValueError, match="4xx or 5xx"):
            ApplicationError("oops", status_code=200)


class TestGenericExceptionHandler:
    def test_an_unhandled_exception_returns_a_generic_500_without_leaking_details(self, client):
        response = client.get("/unhandled")

        assert response.status_code == 500
        assert response.json() == {"detail": "Internal server error"}
