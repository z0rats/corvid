import asyncio
import json

from app.features.instagram_search.service import instagram_session_service


def _run(coro):
    return asyncio.run(coro)


class _FakeApikey:
    def __init__(self, key: str, is_active: bool = True):
        self.key = key
        self.is_active = is_active


VALID_SESSION = {"sessionid": "abc123", "csrftoken": "def456", "ds_user_id": "789"}


def test_returns_none_when_no_row_exists(monkeypatch):
    async def _fake_get_apikey(db, name):
        assert name == "instagram_session"
        return None

    monkeypatch.setattr(instagram_session_service, "get_apikey", _fake_get_apikey)
    assert _run(instagram_session_service.get_session_dict(db=None)) is None


def test_returns_none_when_key_is_inactive(monkeypatch):
    async def _fake_get_apikey(db, name):
        return _FakeApikey(json.dumps(VALID_SESSION), is_active=False)

    monkeypatch.setattr(instagram_session_service, "get_apikey", _fake_get_apikey)
    assert _run(instagram_session_service.get_session_dict(db=None)) is None


def test_returns_none_when_key_is_blank(monkeypatch):
    async def _fake_get_apikey(db, name):
        return _FakeApikey("", is_active=True)

    monkeypatch.setattr(instagram_session_service, "get_apikey", _fake_get_apikey)
    assert _run(instagram_session_service.get_session_dict(db=None)) is None


def test_returns_none_for_invalid_json(monkeypatch):
    async def _fake_get_apikey(db, name):
        return _FakeApikey("not json at all", is_active=True)

    monkeypatch.setattr(instagram_session_service, "get_apikey", _fake_get_apikey)
    assert _run(instagram_session_service.get_session_dict(db=None)) is None


def test_returns_none_for_json_that_is_not_a_dict(monkeypatch):
    async def _fake_get_apikey(db, name):
        return _FakeApikey(json.dumps(["sessionid", "csrftoken"]), is_active=True)

    monkeypatch.setattr(instagram_session_service, "get_apikey", _fake_get_apikey)
    assert _run(instagram_session_service.get_session_dict(db=None)) is None


def test_returns_none_when_missing_a_required_key(monkeypatch):
    incomplete = {"sessionid": "abc123", "csrftoken": "def456"}

    async def _fake_get_apikey(db, name):
        return _FakeApikey(json.dumps(incomplete), is_active=True)

    monkeypatch.setattr(instagram_session_service, "get_apikey", _fake_get_apikey)
    assert _run(instagram_session_service.get_session_dict(db=None)) is None


def test_returns_none_when_a_required_key_is_empty(monkeypatch):
    invalid = {"sessionid": "", "csrftoken": "def456", "ds_user_id": "789"}

    async def _fake_get_apikey(db, name):
        return _FakeApikey(json.dumps(invalid), is_active=True)

    monkeypatch.setattr(instagram_session_service, "get_apikey", _fake_get_apikey)
    assert _run(instagram_session_service.get_session_dict(db=None)) is None


def test_returns_session_dict_when_valid(monkeypatch):
    async def _fake_get_apikey(db, name):
        return _FakeApikey(json.dumps(VALID_SESSION), is_active=True)

    monkeypatch.setattr(instagram_session_service, "get_apikey", _fake_get_apikey)
    assert _run(instagram_session_service.get_session_dict(db=None)) == VALID_SESSION


def test_extra_cookie_keys_are_preserved(monkeypatch):
    """A user pasting more than the minimal 3 cookies shouldn't be rejected."""
    extra = {**VALID_SESSION, "mid": "someMidValue"}

    async def _fake_get_apikey(db, name):
        return _FakeApikey(json.dumps(extra), is_active=True)

    monkeypatch.setattr(instagram_session_service, "get_apikey", _fake_get_apikey)
    assert _run(instagram_session_service.get_session_dict(db=None)) == extra


def test_is_session_configured_reflects_validity(monkeypatch):
    async def _fake_get_apikey_valid(db, name):
        return _FakeApikey(json.dumps(VALID_SESSION), is_active=True)

    monkeypatch.setattr(instagram_session_service, "get_apikey", _fake_get_apikey_valid)
    assert _run(instagram_session_service.is_session_configured(db=None)) is True

    async def _fake_get_apikey_none(db, name):
        return None

    monkeypatch.setattr(instagram_session_service, "get_apikey", _fake_get_apikey_none)
    assert _run(instagram_session_service.is_session_configured(db=None)) is False
