"""parse_ghunt_session replicates GHunt's own GHuntCreds.are_creds_loaded() structural check
(cookies/osids/android.master_token all truthy) without ever running the GHunt CLI - see
docs/architecture/ghunt.md. save_ghunt_session is exercised against monkeypatched
create_apikey_service/update_apikey_service, mirroring test_instagram_session_service.py's
fake-get_apikey style for the rest of this module's dependencies.
"""

import asyncio
import base64
import json
from types import SimpleNamespace

import pytest

from app.core.exceptions import AppHTTPException
from app.features.email_search.service import ghunt_session_service


def _run(coro):
    return asyncio.run(coro)


def _valid_session() -> dict:
    return {
        "cookies": {"SID": "abc", "HSID": "def"},
        "osids": {"1": "osid-value"},
        "android": {"master_token": "aas_et/token", "authorization_tokens": {}},
    }


def _encode(data: dict) -> str:
    return base64.b64encode(json.dumps(data).encode()).decode()


VALID_SESSION_VALUE = _encode(_valid_session())


class TestParseGhuntSession:
    def test_valid_session_returns_the_decoded_dict(self):
        assert ghunt_session_service.parse_ghunt_session(VALID_SESSION_VALUE) == _valid_session()

    def test_blank_value_is_none(self):
        assert ghunt_session_service.parse_ghunt_session("") is None
        assert ghunt_session_service.parse_ghunt_session("   ") is None

    def test_not_base64_is_none(self):
        assert ghunt_session_service.parse_ghunt_session("not-base64-!!!") is None

    def test_base64_of_non_json_is_none(self):
        value = base64.b64encode(b"not json at all").decode()
        assert ghunt_session_service.parse_ghunt_session(value) is None

    def test_base64_of_a_json_list_is_none(self):
        value = base64.b64encode(json.dumps(["a", "b"]).encode()).decode()
        assert ghunt_session_service.parse_ghunt_session(value) is None

    def test_missing_cookies_is_none(self):
        data = _valid_session()
        del data["cookies"]
        assert ghunt_session_service.parse_ghunt_session(_encode(data)) is None

    def test_empty_cookies_is_none(self):
        data = _valid_session()
        data["cookies"] = {}
        assert ghunt_session_service.parse_ghunt_session(_encode(data)) is None

    def test_missing_osids_is_none(self):
        data = _valid_session()
        del data["osids"]
        assert ghunt_session_service.parse_ghunt_session(_encode(data)) is None

    def test_missing_android_section_is_none(self):
        data = _valid_session()
        del data["android"]
        assert ghunt_session_service.parse_ghunt_session(_encode(data)) is None

    def test_android_not_a_dict_is_none(self):
        data = _valid_session()
        data["android"] = "not-a-dict"
        assert ghunt_session_service.parse_ghunt_session(_encode(data)) is None

    def test_missing_master_token_is_none(self):
        data = _valid_session()
        data["android"] = {"authorization_tokens": {}}
        assert ghunt_session_service.parse_ghunt_session(_encode(data)) is None

    def test_empty_master_token_is_none(self):
        data = _valid_session()
        data["android"]["master_token"] = ""
        assert ghunt_session_service.parse_ghunt_session(_encode(data)) is None

    def test_extra_fields_are_preserved(self):
        data = _valid_session()
        data["some_future_field"] = "kept as-is"
        assert ghunt_session_service.parse_ghunt_session(_encode(data)) == data


class TestSaveGhuntSession:
    def test_invalid_session_raises_without_touching_storage(self, monkeypatch):
        calls = []

        async def fake_update(*args, **kwargs):
            calls.append("update")

        async def fake_create(*args, **kwargs):
            calls.append("create")

        monkeypatch.setattr(ghunt_session_service, "update_apikey_service", fake_update)
        monkeypatch.setattr(ghunt_session_service, "create_apikey_service", fake_create)

        with pytest.raises(AppHTTPException) as exc_info:
            _run(ghunt_session_service.save_ghunt_session(db=None, value="not-a-valid-session"))

        assert exc_info.value.status_code == 400
        assert exc_info.value.error_code == "GHUNT_SESSION_INVALID"
        assert calls == []

    def test_updates_an_existing_row_when_present(self, monkeypatch):
        captured = {}

        async def fake_update(db, name, data):
            captured["name"] = name
            captured["key"] = data.key
            return SimpleNamespace(name=name, is_active=True)

        async def fake_create(*args, **kwargs):
            raise AssertionError("should not create when update succeeds")

        monkeypatch.setattr(ghunt_session_service, "update_apikey_service", fake_update)
        monkeypatch.setattr(ghunt_session_service, "create_apikey_service", fake_create)

        result = _run(ghunt_session_service.save_ghunt_session(db=None, value=VALID_SESSION_VALUE))

        assert result.name == "ghunt_session"
        assert result.is_active is True
        assert not hasattr(result, "key")
        assert captured["name"] == "ghunt_session"
        assert captured["key"] == VALID_SESSION_VALUE

    def test_creates_when_no_existing_row(self, monkeypatch):
        async def fake_update(db, name, data):
            return None

        captured = {}

        async def fake_create(db, data):
            captured["name"] = data.name
            captured["key"] = data.key
            return SimpleNamespace(name=data.name, is_active=True)

        monkeypatch.setattr(ghunt_session_service, "update_apikey_service", fake_update)
        monkeypatch.setattr(ghunt_session_service, "create_apikey_service", fake_create)

        result = _run(ghunt_session_service.save_ghunt_session(db=None, value=VALID_SESSION_VALUE))

        assert result.name == "ghunt_session"
        assert result.is_active is True
        assert not hasattr(result, "key")
        assert captured["name"] == "ghunt_session"
        assert captured["key"] == VALID_SESSION_VALUE
