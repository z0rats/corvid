"""Covers only the parameter-passing/response-mapping contract of the two
PyPI-update-check endpoints (`/info`, `/check-update`) - the actual fetch/record/
compute logic they delegate to now lives in `core/utils/pypi_version_check.py`
and is covered there (`test_pypi_version_check.py`).
"""

from types import SimpleNamespace

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.core.dependencies import get_db, get_read_db
from app.core.utils.pypi_version_check import UpdateCheckResult
from app.features.email_search.routers import email_search_routes


@pytest.fixture
def client():
    app = FastAPI()
    app.include_router(email_search_routes.router)
    app.dependency_overrides[get_read_db] = lambda: None
    app.dependency_overrides[get_db] = lambda: None
    return TestClient(app)


def _fake_config(**overrides):
    defaults = dict(
        latest_pypi_version=None, enable_smtp_checks=False, enable_headless_checks=False
    )
    return SimpleNamespace(**{**defaults, **overrides})


class TestReadInfo:
    def test_maps_config_and_computed_update_availability_into_response(self, client, monkeypatch):
        config = _fake_config(latest_pypi_version="2.0.0", enable_smtp_checks=True)

        async def fake_get_config(db):
            return config

        monkeypatch.setattr(email_search_routes, "get_email_search_config", fake_get_config)
        monkeypatch.setattr(email_search_routes, "get_installed_version", lambda: "1.0.0")

        response = client.get("/api/email-search/info")

        assert response.status_code == 200
        body = response.json()
        assert body["tool"] == "mailcat"
        assert body["version"] == "1.0.0"
        assert body["latest_version"] == "2.0.0"
        assert body["update_available"] is True
        # provider_count reflects the config's own enable flags, not the update-check plumbing
        assert body["provider_count"] > len(email_search_routes.DEFAULT_CHECKERS)

    def test_update_available_is_null_when_never_checked(self, client, monkeypatch):
        config = _fake_config(latest_pypi_version=None)

        async def fake_get_config(db):
            return config

        monkeypatch.setattr(email_search_routes, "get_email_search_config", fake_get_config)
        monkeypatch.setattr(email_search_routes, "get_installed_version", lambda: "1.0.0")

        response = client.get("/api/email-search/info")

        assert response.status_code == 200
        assert response.json()["update_available"] is None


def _patch_config(monkeypatch, **overrides):
    config = _fake_config(**{"proxy_url": None, "use_tor": False, **overrides})

    async def fake_get_config(db):
        return config

    monkeypatch.setattr(email_search_routes, "get_email_search_config", fake_get_config)


class TestReadInfoUserScanner:
    def test_reports_the_installed_version_and_runnable_module_count(self, client, monkeypatch):
        _patch_config(monkeypatch)
        monkeypatch.setattr(email_search_routes, "user_scanner_available", lambda: True)
        monkeypatch.setattr(email_search_routes, "get_user_scanner_version", lambda: "1.5.2.1")
        monkeypatch.setattr(email_search_routes, "runnable_module_count", lambda: 152)

        response = client.get("/api/email-search/info", params={"source": "user_scanner"})

        assert response.json() == {
            "tool": "user-scanner",
            "version": "1.5.2.1",
            "provider_count": 152,
            "available": True,
            "blocked_reason": None,
            "latest_version": None,
            "update_available": None,
        }

    def test_flags_a_missing_package_instead_of_failing(self, client, monkeypatch):
        _patch_config(monkeypatch)
        monkeypatch.setattr(email_search_routes, "user_scanner_available", lambda: False)
        monkeypatch.setattr(email_search_routes, "runnable_module_count", lambda: 152)

        body = client.get("/api/email-search/info", params={"source": "user_scanner"}).json()

        assert body["available"] is False
        assert body["version"] == ""

    @pytest.mark.parametrize("routing", [{"use_tor": True}, {"proxy_url": "socks5://p:1080"}])
    def test_warns_up_front_that_tor_or_a_proxy_blocks_the_scan(self, client, monkeypatch, routing):
        _patch_config(monkeypatch, **routing)
        monkeypatch.setattr(email_search_routes, "user_scanner_available", lambda: True)
        monkeypatch.setattr(email_search_routes, "get_user_scanner_version", lambda: "1.5.2.1")
        monkeypatch.setattr(email_search_routes, "runnable_module_count", lambda: 152)

        body = client.get("/api/email-search/info", params={"source": "user_scanner"}).json()

        assert body["blocked_reason"] == email_search_routes.PROXY_UNSUPPORTED_MESSAGE


class TestCheckUpdate:
    def test_delegates_to_check_for_update_with_package_name_config_and_installed_version(
        self, client, monkeypatch
    ):
        config = _fake_config()
        captured = {}

        async def fake_get_config(db):
            return config

        async def fake_check_for_update(db, package_name, passed_config, installed_version):
            captured["package_name"] = package_name
            captured["config"] = passed_config
            captured["installed_version"] = installed_version
            return UpdateCheckResult(latest_version="9.9.9", update_available=True)

        monkeypatch.setattr(email_search_routes, "get_email_search_config", fake_get_config)
        monkeypatch.setattr(email_search_routes, "get_installed_version", lambda: "1.0.0")
        monkeypatch.setattr(email_search_routes, "check_for_update", fake_check_for_update)

        response = client.post("/api/email-search/check-update")

        assert response.status_code == 200
        assert captured["package_name"] == email_search_routes.PACKAGE_NAME
        assert captured["config"] is config
        assert captured["installed_version"] == "1.0.0"

        body = response.json()
        assert body["latest_version"] == "9.9.9"
        assert body["update_available"] is True
        assert body["version"] == "1.0.0"
