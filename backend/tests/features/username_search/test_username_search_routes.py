"""Covers only the parameter-passing/response-mapping contract of the PyPI-update-check
endpoints (`/info`, `/maigret/check-update`, `/social-analyzer/check-update`) - the actual
fetch/record/compute logic they delegate to now lives in `core/utils/pypi_version_check.py`
and is covered there (`test_pypi_version_check.py`).
"""
from types import SimpleNamespace

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from app.core.config.rate_limit_config import limiter
from app.core.dependencies import get_db, get_read_db
from app.core.utils.pypi_version_check import UpdateCheckResult
from app.features.username_search.routers import username_search_routes


@pytest.fixture
def client():
    app = FastAPI()
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
    app.include_router(username_search_routes.router)
    app.dependency_overrides[get_read_db] = lambda: None
    app.dependency_overrides[get_db] = lambda: None
    return TestClient(app)


def _fake_maigret_config(**overrides):
    defaults = dict(latest_pypi_version=None, db_site_count=1234, db_last_updated_at=None)
    return SimpleNamespace(**{**defaults, **overrides})


def _fake_sa_config(**overrides):
    defaults = dict(latest_pypi_version=None)
    return SimpleNamespace(**{**defaults, **overrides})


@pytest.fixture(autouse=True)
def _stub_installed_versions(monkeypatch):
    """Isolate these tests from the real installed maigret/social-analyzer packages."""
    monkeypatch.setattr(username_search_routes.maigret, "__version__", "1.0.0")
    monkeypatch.setattr(username_search_routes, "get_social_analyzer_version", lambda: "2.0.0")
    monkeypatch.setattr(username_search_routes, "get_bundled_site_count", lambda: 500)


class TestReadInfo:
    def test_maps_both_tools_configs_and_computed_update_availability(self, client, monkeypatch):
        maigret_config = _fake_maigret_config(latest_pypi_version="1.5.0")
        sa_config = _fake_sa_config(latest_pypi_version=None)

        async def fake_get_maigret_config(db):
            return maigret_config

        async def fake_get_sa_config(db):
            return sa_config

        monkeypatch.setattr(username_search_routes, "get_username_search_config", fake_get_maigret_config)
        monkeypatch.setattr(username_search_routes, "get_social_analyzer_config", fake_get_sa_config)

        response = client.get("/api/username-search/info")

        assert response.status_code == 200
        body = response.json()
        maigret_info, sa_info = body[0], body[1]

        assert maigret_info["tool"] == "maigret"
        assert maigret_info["latest_version"] == "1.5.0"
        assert maigret_info["update_available"] is True

        assert sa_info["tool"] == "social_analyzer"
        assert sa_info["latest_version"] is None
        assert sa_info["update_available"] is None


class TestCheckMaigretUpdate:
    def test_delegates_to_check_for_update_with_package_name_config_and_installed_version(self, client, monkeypatch):
        config = _fake_maigret_config()
        captured = {}

        async def fake_get_config(db):
            return config

        async def fake_check_for_update(db, package_name, passed_config, installed_version):
            captured["package_name"] = package_name
            captured["config"] = passed_config
            captured["installed_version"] = installed_version
            return UpdateCheckResult(latest_version="9.9.9", update_available=True)

        monkeypatch.setattr(username_search_routes, "get_username_search_config", fake_get_config)
        monkeypatch.setattr(username_search_routes, "check_for_update", fake_check_for_update)

        response = client.post("/api/username-search/maigret/check-update")

        assert response.status_code == 200
        assert captured["package_name"] == username_search_routes.MAIGRET_PACKAGE_NAME
        assert captured["config"] is config
        assert captured["installed_version"] == "1.0.0"

        body = response.json()
        assert body["tool"] == "maigret"
        assert body["latest_version"] == "9.9.9"
        assert body["update_available"] is True


class TestCheckSocialAnalyzerUpdate:
    def test_delegates_to_check_for_update_with_package_name_config_and_installed_version(self, client, monkeypatch):
        config = _fake_sa_config()
        captured = {}

        async def fake_get_config(db):
            return config

        async def fake_check_for_update(db, package_name, passed_config, installed_version):
            captured["package_name"] = package_name
            captured["config"] = passed_config
            captured["installed_version"] = installed_version
            return UpdateCheckResult(latest_version=None, update_available=None)

        monkeypatch.setattr(username_search_routes, "get_social_analyzer_config", fake_get_config)
        monkeypatch.setattr(username_search_routes, "check_for_update", fake_check_for_update)

        response = client.post("/api/username-search/social-analyzer/check-update")

        assert response.status_code == 200
        assert captured["package_name"] == username_search_routes.SOCIAL_ANALYZER_PACKAGE_NAME
        assert captured["config"] is config
        assert captured["installed_version"] == "2.0.0"

        body = response.json()
        assert body["tool"] == "social_analyzer"
        assert body["latest_version"] is None
        assert body["update_available"] is None
