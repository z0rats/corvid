import asyncio

from app.core.settings.api_keys.config.service_config import SERVICE_DEFINITIONS
from app.features.steam_recon.service import steam_api_key_service


def _run(coro):
    return asyncio.run(coro)


class _FakeApikey:
    def __init__(self, key: str, is_active: bool = True):
        self.key = key
        self.is_active = is_active


def test_returns_none_when_no_row_exists(monkeypatch):
    async def _fake_get_apikey(db, name):
        assert name == "steam"
        return None

    monkeypatch.setattr(steam_api_key_service, "get_apikey", _fake_get_apikey)
    assert _run(steam_api_key_service.get_steam_api_key(db=None)) is None


def test_returns_none_when_key_is_inactive(monkeypatch):
    async def _fake_get_apikey(db, name):
        return _FakeApikey("test-key", is_active=False)

    monkeypatch.setattr(steam_api_key_service, "get_apikey", _fake_get_apikey)
    assert _run(steam_api_key_service.get_steam_api_key(db=None)) is None


def test_returns_none_when_key_is_blank(monkeypatch):
    async def _fake_get_apikey(db, name):
        return _FakeApikey("", is_active=True)

    monkeypatch.setattr(steam_api_key_service, "get_apikey", _fake_get_apikey)
    assert _run(steam_api_key_service.get_steam_api_key(db=None)) is None


def test_returns_key_when_active_and_configured(monkeypatch):
    async def _fake_get_apikey(db, name):
        return _FakeApikey("test-key", is_active=True)

    monkeypatch.setattr(steam_api_key_service, "get_apikey", _fake_get_apikey)
    assert _run(steam_api_key_service.get_steam_api_key(db=None)) == "test-key"


def test_settings_ui_lists_the_key_name_the_service_reads():
    """The Settings > API Keys row and the lookup must agree on the key name, or a key
    entered in the UI is never found."""
    definition = SERVICE_DEFINITIONS[steam_api_key_service.STEAM_API_KEY_NAME]
    assert definition.required_keys == [steam_api_key_service.STEAM_API_KEY_NAME]
