"""Covers the two bulk-lookup routes' interaction with keyless providers
(core/settings/api_keys/service/keyless_providers.py) - previously untested."""
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.core.dependencies import get_db, get_read_db
from app.core.settings.api_keys.routers import api_keys_settings_routes
from app.core.settings.api_keys.schemas.api_keys_settings_schemas import ApikeySchema
from app.core.settings.api_keys.service import keyless_providers


@pytest.fixture
def client():
    app = FastAPI()
    app.include_router(api_keys_settings_routes.router)
    app.dependency_overrides[get_read_db] = lambda: None
    app.dependency_overrides[get_db] = lambda: None
    return TestClient(app)


@pytest.fixture(autouse=True)
def _reset_keyless_providers():
    keyless_providers.set_keyless_provider_names(set())
    yield
    keyless_providers.set_keyless_provider_names(set())


class TestGetAllApikeysBulkLookup:
    def test_includes_keyless_providers_not_in_db_as_enabled(self, client, monkeypatch):
        async def fake_get_all_apikeys_bulk_lookup_status(db):
            return {"abuseipdb": False}

        monkeypatch.setattr(
            api_keys_settings_routes, "get_all_apikeys_bulk_lookup_status", fake_get_all_apikeys_bulk_lookup_status,
        )
        keyless_providers.set_keyless_provider_names({"urlscan"})

        response = client.get("/api/apikeys/bulk_ioc_lookup")

        assert response.status_code == 200
        assert response.json() == {"abuseipdb": False, "urlscan": True}

    def test_db_record_for_a_keyless_provider_is_not_overridden(self, client, monkeypatch):
        async def fake_get_all_apikeys_bulk_lookup_status(db):
            return {"urlscan": False}

        monkeypatch.setattr(
            api_keys_settings_routes, "get_all_apikeys_bulk_lookup_status", fake_get_all_apikeys_bulk_lookup_status,
        )
        keyless_providers.set_keyless_provider_names({"urlscan"})

        response = client.get("/api/apikeys/bulk_ioc_lookup")

        assert response.json() == {"urlscan": False}


class TestUpdateApikeyBulkLookup:
    def test_keyless_service_without_db_row_is_upserted(self, client, monkeypatch):
        async def fake_update_apikey_bulk_lookup_status(db, name, bulk_ioc_lookup):
            return None

        async def fake_upsert_apikey_bulk_lookup_status(db, name, bulk_ioc_lookup):
            return ApikeySchema(name=name, bulk_ioc_lookup=bulk_ioc_lookup)

        monkeypatch.setattr(
            api_keys_settings_routes, "update_apikey_bulk_lookup_status", fake_update_apikey_bulk_lookup_status,
        )
        monkeypatch.setattr(
            api_keys_settings_routes, "upsert_apikey_bulk_lookup_status", fake_upsert_apikey_bulk_lookup_status,
        )
        keyless_providers.set_keyless_provider_names({"urlscan"})

        response = client.patch("/api/apikeys/urlscan/bulk_ioc_lookup", json={"bulk_ioc_lookup": True})

        assert response.status_code == 200
        assert response.json()["name"] == "urlscan"
        assert response.json()["bulk_ioc_lookup"] is True

    def test_keyed_service_without_db_row_returns_404(self, client, monkeypatch):
        async def fake_update_apikey_bulk_lookup_status(db, name, bulk_ioc_lookup):
            return None

        monkeypatch.setattr(
            api_keys_settings_routes, "update_apikey_bulk_lookup_status", fake_update_apikey_bulk_lookup_status,
        )
        keyless_providers.set_keyless_provider_names({"urlscan"})

        response = client.patch("/api/apikeys/abuseipdb/bulk_ioc_lookup", json={"bulk_ioc_lookup": True})

        assert response.status_code == 404
