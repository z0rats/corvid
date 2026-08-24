import asyncio

from app.features.image_tools.service import google_maps_service


def _run(coro):
    return asyncio.run(coro)


class _FakeApikey:
    def __init__(self, key: str, is_active: bool = True):
        self.key = key
        self.is_active = is_active


def test_returns_none_when_no_row_exists(monkeypatch):
    async def _fake_get_apikey(db, name):
        assert name == "google_maps"
        return None

    monkeypatch.setattr(google_maps_service, "get_apikey", _fake_get_apikey)
    assert _run(google_maps_service.get_google_maps_key(db=None)) is None


def test_returns_none_when_key_is_inactive(monkeypatch):
    async def _fake_get_apikey(db, name):
        return _FakeApikey("test-key", is_active=False)

    monkeypatch.setattr(google_maps_service, "get_apikey", _fake_get_apikey)
    assert _run(google_maps_service.get_google_maps_key(db=None)) is None


def test_returns_none_when_key_is_blank(monkeypatch):
    async def _fake_get_apikey(db, name):
        return _FakeApikey("", is_active=True)

    monkeypatch.setattr(google_maps_service, "get_apikey", _fake_get_apikey)
    assert _run(google_maps_service.get_google_maps_key(db=None)) is None


def test_returns_key_when_active_and_configured(monkeypatch):
    async def _fake_get_apikey(db, name):
        return _FakeApikey("test-key", is_active=True)

    monkeypatch.setattr(google_maps_service, "get_apikey", _fake_get_apikey)
    assert _run(google_maps_service.get_google_maps_key(db=None)) == "test-key"
