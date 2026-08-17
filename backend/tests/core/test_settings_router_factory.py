import pytest
from fastapi import FastAPI, status
from fastapi.testclient import TestClient
from pydantic import BaseModel

from app.core.dependencies import get_db, get_read_db
from app.core.exceptions import AppHTTPException, register_exception_handlers
from app.core.settings.settings_router_factory import build_singleton_settings_router


class FakeResponse(BaseModel):
    id: int
    name: str
    optional_field: str | None = None


class FakeUpdate(BaseModel):
    name: str | None = None


async def _noop_db():
    yield None


def _build_client(router, *, register_handlers: bool = False):
    app = FastAPI()
    if register_handlers:
        register_exception_handlers(app)
    app.include_router(router)
    app.dependency_overrides[get_db] = _noop_db
    app.dependency_overrides[get_read_db] = _noop_db
    return TestClient(app)


class TestGetRoute:
    def test_returns_get_service_result_validated_against_response_schema(self):
        async def fake_get_service(db):
            return {"id": 1, "name": "stored"}

        router = build_singleton_settings_router(
            prefix="/thing",
            tags=["Thing"],
            response_schema=FakeResponse,
            update_schema=FakeUpdate,
            get_service=fake_get_service,
            update_service=lambda db, payload: None,
        )
        client = _build_client(router)

        response = client.get("/thing")

        assert response.status_code == 200
        assert response.json() == {"id": 1, "name": "stored", "optional_field": None}


class TestPutRoute:
    def test_calls_update_service_with_parsed_body_and_returns_its_validated_result(self):
        received = {}

        async def fake_update_service(db, payload):
            received["payload"] = payload
            return {"id": 1, "name": payload.name}

        router = build_singleton_settings_router(
            prefix="/thing",
            tags=["Thing"],
            response_schema=FakeResponse,
            update_schema=FakeUpdate,
            get_service=lambda db: None,
            update_service=fake_update_service,
        )
        client = _build_client(router)

        response = client.put("/thing", json={"name": "updated"})

        assert response.status_code == 200
        assert response.json() == {"id": 1, "name": "updated", "optional_field": None}
        assert isinstance(received["payload"], FakeUpdate)
        assert received["payload"].name == "updated"


class TestOnAfterUpdate:
    def test_called_once_with_payload_and_result_after_update_service_returns(self):
        calls = []

        async def fake_update_service(db, payload):
            assert not calls, "on_after_update must run after update_service, not before"
            return {"id": 1, "name": payload.name}

        def on_after_update(payload, result):
            calls.append((payload, result))

        router = build_singleton_settings_router(
            prefix="/thing",
            tags=["Thing"],
            response_schema=FakeResponse,
            update_schema=FakeUpdate,
            get_service=lambda db: None,
            update_service=fake_update_service,
            on_after_update=on_after_update,
        )
        client = _build_client(router)

        response = client.put("/thing", json={"name": "updated"})

        assert response.status_code == 200
        assert len(calls) == 1
        payload, result = calls[0]
        assert payload.name == "updated"
        assert result == {"id": 1, "name": "updated"}

    def test_not_called_when_omitted(self):
        def boom(*args, **kwargs):
            raise AssertionError("on_after_update should not be invoked when omitted")

        async def fake_update_service(db, payload):
            return {"id": 1, "name": payload.name}

        router = build_singleton_settings_router(
            prefix="/thing",
            tags=["Thing"],
            response_schema=FakeResponse,
            update_schema=FakeUpdate,
            get_service=lambda db: None,
            update_service=fake_update_service,
        )
        client = _build_client(router)

        response = client.put("/thing", json={"name": "updated"})

        assert response.status_code == 200


def _mapped_error(exc: Exception, op: str) -> None:
    raise AppHTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail=f"mapped:{op}",
        error_code="MAPPED",
    ) from exc


class TestOnError:
    def test_get_service_error_is_passed_to_on_error_with_get_op(self):
        calls = []

        async def failing_get_service(db):
            raise RuntimeError("get boom")

        def on_error(exc, op):
            calls.append((exc, op))
            _mapped_error(exc, op)

        router = build_singleton_settings_router(
            prefix="/thing",
            tags=["Thing"],
            response_schema=FakeResponse,
            update_schema=FakeUpdate,
            get_service=failing_get_service,
            update_service=lambda db, payload: None,
            on_error=on_error,
        )
        client = _build_client(router, register_handlers=True)

        response = client.get("/thing")

        assert response.status_code == 400
        assert response.json()["error_code"] == "MAPPED"
        assert len(calls) == 1
        exc, op = calls[0]
        assert isinstance(exc, RuntimeError)
        assert op == "get"

    def test_update_service_error_is_passed_to_on_error_with_update_op(self):
        calls = []

        async def failing_update_service(db, payload):
            raise RuntimeError("update boom")

        def on_error(exc, op):
            calls.append((exc, op))
            _mapped_error(exc, op)

        router = build_singleton_settings_router(
            prefix="/thing",
            tags=["Thing"],
            response_schema=FakeResponse,
            update_schema=FakeUpdate,
            get_service=lambda db: None,
            update_service=failing_update_service,
            on_error=on_error,
        )
        client = _build_client(router, register_handlers=True)

        response = client.put("/thing", json={"name": "x"})

        assert response.status_code == 400
        assert response.json()["error_code"] == "MAPPED"
        assert len(calls) == 1
        exc, op = calls[0]
        assert isinstance(exc, RuntimeError)
        assert op == "update"

    def test_on_after_update_not_called_when_update_service_errors(self):
        def boom(*args, **kwargs):
            raise AssertionError("on_after_update should not run when update_service raised")

        async def failing_update_service(db, payload):
            raise RuntimeError("update boom")

        router = build_singleton_settings_router(
            prefix="/thing",
            tags=["Thing"],
            response_schema=FakeResponse,
            update_schema=FakeUpdate,
            get_service=lambda db: None,
            update_service=failing_update_service,
            on_after_update=boom,
            on_error=_mapped_error,
        )
        client = _build_client(router, register_handlers=True)

        response = client.put("/thing", json={"name": "x"})

        assert response.status_code == 400

    def test_error_propagates_unchanged_when_on_error_omitted(self):
        async def failing_get_service(db):
            raise RuntimeError("get boom")

        router = build_singleton_settings_router(
            prefix="/thing",
            tags=["Thing"],
            response_schema=FakeResponse,
            update_schema=FakeUpdate,
            get_service=failing_get_service,
            update_service=lambda db, payload: None,
        )
        client = _build_client(router)

        with pytest.raises(RuntimeError, match="get boom"):
            client.get("/thing")


class TestExcludeNone:
    @pytest.mark.parametrize("exclude_none", [True, False])
    def test_sets_response_model_exclude_none_on_both_routes(self, exclude_none):
        router = build_singleton_settings_router(
            prefix="/thing",
            tags=["Thing"],
            response_schema=FakeResponse,
            update_schema=FakeUpdate,
            get_service=lambda db: None,
            update_service=lambda db, payload: None,
            exclude_none=exclude_none,
        )

        routes_by_method = {method: route for route in router.routes for method in route.methods}

        assert routes_by_method["GET"].response_model_exclude_none is exclude_none
        assert routes_by_method["PUT"].response_model_exclude_none is exclude_none
