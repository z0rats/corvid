"""`/api/services/*`: the static service catalogue joined with which API keys
are configured/active - and never the key values themselves."""

from collections.abc import AsyncGenerator

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_db, get_read_db
from app.core.exceptions import register_exception_handlers
from app.core.settings.api_keys.config.service_config import SERVICE_DEFINITIONS
from app.core.settings.api_keys.models.api_keys_settings_models import Apikey
from app.core.settings.api_keys.routers.service_config_routes import router
from app.core.settings.api_keys.service import service_config_service
from tests.conftest import run

SECRET = "sk-super-secret-value-123"


@pytest.fixture
def client(make_session_factory):
    session_factory = make_session_factory([Apikey.__table__])

    async def _seed():
        async with session_factory() as db:
            db.add_all(
                [
                    Apikey(name="virustotal", key=SECRET, is_active=True),
                    Apikey(name="crowdstrike_client_id", key=SECRET, is_active=True),
                    Apikey(name="crowdstrike_client_secret", key=SECRET, is_active=False),
                ]
            )
            await db.commit()

    run(_seed())

    async def _get_db() -> AsyncGenerator[AsyncSession]:
        async with session_factory() as db:
            yield db

    app = FastAPI()
    register_exception_handlers(app)
    app.include_router(router)
    app.dependency_overrides[get_db] = _get_db
    app.dependency_overrides[get_read_db] = _get_db
    return TestClient(app, raise_server_exceptions=False)


class TestCatalogue:
    def test_full_catalogue_with_key_status_and_no_secrets(self, client):
        r = client.get("/api/services/config")
        assert r.status_code == 200
        body = r.json()
        assert set(body) == set(SERVICE_DEFINITIONS)
        assert SECRET not in r.text

        assert body["virustotal"]["available"] is True
        assert body["virustotal"]["api_key_status"] == {
            "virustotal": {"configured": True, "active": True}
        }
        assert body["abuseipdb"]["available"] is False
        assert body["abuseipdb"]["api_key_status"]["abuseipdb"] == {
            "configured": False,
            "active": False,
        }

    def test_keyless_service_always_available(self, client):
        body = client.get("/api/services/config").json()
        assert body["urlscanio"]["api_key_status"] == {}
        assert body["urlscanio"]["available"] is True

    def test_multi_key_service_needs_every_key_active(self, client):
        cs = client.get("/api/services/config/crowdstrike").json()
        assert cs["available"] is False
        assert cs["api_key_status"]["crowdstrike_client_secret"] == {
            "configured": True,
            "active": False,
        }

    def test_unknown_service_404(self, client):
        r = client.get("/api/services/config/nope")
        assert r.status_code == 404
        assert r.json()["error_code"] == "SERVICE_NOT_FOUND"


class TestFilters:
    def _keys(self, client, **params):
        r = client.get("/api/services/config", params=params)
        assert r.status_code == 200
        return set(r.json())

    def test_single_filters(self, client):
        assert self._keys(client, tier="paid") == {
            k for k, s in SERVICE_DEFINITIONS.items() if s.tier == "paid"
        }
        assert "emailrepio" in self._keys(client, ioc_type="Email")
        assert "abuseipdb" not in self._keys(client, ioc_type="Email")

    def test_filters_combine_rather_than_override(self, client):
        """Regression: each filter used to replace the previous one's result."""
        got = self._keys(client, category="email_identity", tier="paid")
        assert got == {
            k
            for k, s in SERVICE_DEFINITIONS.items()
            if s.category == "email_identity" and s.tier == "paid"
        }
        assert "haveibeenpwned" in got
        assert "hunterio" not in got  # email_identity but freemium
        assert "crowdstrike" not in got  # paid but threat_intelligence

    def test_invalid_enum_value_422(self, client):
        assert client.get("/api/services/config", params={"tier": "gold"}).status_code == 422

    def test_for_ioc_type(self, client):
        body = client.get("/api/services/for-ioc/CVE").json()
        assert set(body) == {
            k for k, s in SERVICE_DEFINITIONS.items() if "CVE" in s.supported_ioc_types
        }
        assert client.get("/api/services/for-ioc/NotAType").json() == {}


class TestEnumerations:
    """Regression: these awaited a plain list and always 500'd."""

    def test_categories(self, client):
        r = client.get("/api/services/categories")
        assert r.status_code == 200
        assert "threat_intelligence" in r.json()

    def test_tiers(self, client):
        r = client.get("/api/services/tiers")
        assert r.status_code == 200
        assert sorted(r.json()) == ["free", "freemium", "paid"]

    def test_ioc_types_sorted_and_unique(self, client):
        types = client.get("/api/services/ioc-types").json()
        assert types == sorted(set(types))
        assert {"IPv4", "Domain", "Email", "CVE"} <= set(types)


def test_db_error_maps_to_500_with_code(client, monkeypatch):
    from sqlalchemy.exc import OperationalError

    async def boom(db):
        raise OperationalError("select", {}, Exception("locked"))

    monkeypatch.setattr(service_config_service, "get_apikeys", boom)
    r = client.get("/api/services/config")
    assert r.status_code == 500
    assert r.json()["error_code"] == "SERVICE_CONFIG_DB_ERROR"
    r = client.get("/api/services/config/virustotal")
    assert r.json()["error_code"] == "SERVICE_CONFIG_DB_ERROR"
    r = client.get("/api/services/for-ioc/IPv4")
    assert r.json()["error_code"] == "SERVICE_CONFIG_DB_ERROR"


def test_config_says_which_services_cannot_be_key_tested(client):
    body = client.get("/api/services/config").json()

    assert body["virustotal"]["key_test_exempt_reason"] is None
    assert "daily allowance" in body["abuseipdb"]["key_test_exempt_reason"]
    # Keyed by the config key, not ServiceDefinition.key ("checkphish").
    assert body["checkphishai"]["key_test_exempt_reason"]
    assert client.get("/api/services/config/abuseipdb").json()["key_test_exempt_reason"]
