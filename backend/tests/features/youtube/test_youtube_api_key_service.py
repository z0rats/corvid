import asyncio

from app.features.youtube.service import youtube_api_key_service


def _run(coro):
    return asyncio.run(coro)


class _FakeApikey:
    def __init__(self, key: str, is_active: bool = True):
        self.key = key
        self.is_active = is_active


def test_returns_none_when_no_row_exists(monkeypatch):
    async def _fake_get_apikey(db, name):
        assert name == "youtube"
        return None

    monkeypatch.setattr(youtube_api_key_service, "get_apikey", _fake_get_apikey)
    assert _run(youtube_api_key_service.get_youtube_api_key(db=None)) is None


def test_returns_none_when_key_is_inactive(monkeypatch):
    async def _fake_get_apikey(db, name):
        return _FakeApikey("test-key", is_active=False)

    monkeypatch.setattr(youtube_api_key_service, "get_apikey", _fake_get_apikey)
    assert _run(youtube_api_key_service.get_youtube_api_key(db=None)) is None


def test_returns_none_when_key_is_blank(monkeypatch):
    async def _fake_get_apikey(db, name):
        return _FakeApikey("", is_active=True)

    monkeypatch.setattr(youtube_api_key_service, "get_apikey", _fake_get_apikey)
    assert _run(youtube_api_key_service.get_youtube_api_key(db=None)) is None


def test_returns_key_when_active_and_configured(monkeypatch):
    async def _fake_get_apikey(db, name):
        return _FakeApikey("test-key", is_active=True)

    monkeypatch.setattr(youtube_api_key_service, "get_apikey", _fake_get_apikey)
    assert _run(youtube_api_key_service.get_youtube_api_key(db=None)) == "test-key"
