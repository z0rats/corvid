"""check_openphish: keyless URL/domain phishing check against OpenPhish's community feed.

Like check_cisa_kev, the free tier has no per-indicator endpoint - only a flat feed of
URLs - so this fetches-and-caches the whole feed in-process on a TTL rather than making
one request per lookup.
"""

import httpx
import pytest

from app.features.ioc_tools.ioc_lookup.single_lookup.service import external_api_clients
from app.features.ioc_tools.ioc_lookup.single_lookup.service.client_base import (
    ServiceError,
    ServiceUnavailableError,
)
from tests.conftest import run as _run


def _response(status_code: int, text: str = "") -> httpx.Response:
    request = httpx.Request("GET", "https://openphish.example/feed.txt")
    return httpx.Response(status_code, request=request, text=text)


class _FakeClient:
    """Records every call made against it and returns a canned response."""

    def __init__(self, response: httpx.Response | None = None, error: Exception | None = None):
        self._response = response
        self._error = error
        self.calls: list[dict] = []

    async def get(self, url, **kwargs):
        self.calls.append({"url": url, **kwargs})
        if self._error is not None:
            raise self._error
        return self._response


def _patch_client(monkeypatch, response=None, error=None) -> _FakeClient:
    fake = _FakeClient(response=response, error=error)
    monkeypatch.setattr(external_api_clients, "get_client", lambda: fake)
    return fake


@pytest.fixture(autouse=True)
def _reset_openphish_cache(monkeypatch):
    """Every test starts from a cold feed cache, so fetch behavior is deterministic."""
    monkeypatch.setitem(external_api_clients._openphish_cache, "urls", None)
    monkeypatch.setitem(external_api_clients._openphish_cache, "domains", None)
    monkeypatch.setitem(external_api_clients._openphish_cache, "fetched_at", 0.0)


_FEED_TEXT = "http://evil.example.com/login\nhttp://sub.other.example/pay\n"


class TestCheckOpenphish:
    def test_listed_url_returns_match(self, monkeypatch):
        _patch_client(monkeypatch, response=_response(200, _FEED_TEXT))

        result = _run(external_api_clients.check_openphish("http://evil.example.com/login"))

        assert result == {"listed": True, "matched_urls": ["http://evil.example.com/login"]}

    def test_unlisted_url_returns_not_listed(self, monkeypatch):
        _patch_client(monkeypatch, response=_response(200, _FEED_TEXT))

        result = _run(external_api_clients.check_openphish("http://clean.example.com/"))

        assert result == {"listed": False, "matched_urls": []}

    def test_listed_domain_returns_matching_urls(self, monkeypatch):
        _patch_client(monkeypatch, response=_response(200, _FEED_TEXT))

        result = _run(external_api_clients.check_openphish("evil.example.com"))

        assert result == {"listed": True, "matched_urls": ["http://evil.example.com/login"]}

    def test_domain_lookup_is_case_insensitive(self, monkeypatch):
        _patch_client(monkeypatch, response=_response(200, _FEED_TEXT))

        result = _run(external_api_clients.check_openphish("EVIL.EXAMPLE.COM"))

        assert result["listed"] is True

    def test_unlisted_domain_returns_not_listed(self, monkeypatch):
        _patch_client(monkeypatch, response=_response(200, _FEED_TEXT))

        result = _run(external_api_clients.check_openphish("clean.example.com"))

        assert result == {"listed": False, "matched_urls": []}

    def test_second_lookup_reuses_cached_feed(self, monkeypatch):
        fake = _patch_client(monkeypatch, response=_response(200, _FEED_TEXT))

        _run(external_api_clients.check_openphish("evil.example.com"))
        _run(external_api_clients.check_openphish("clean.example.com"))

        assert len(fake.calls) == 1

    def test_expired_cache_triggers_refetch(self, monkeypatch):
        fake = _patch_client(monkeypatch, response=_response(200, _FEED_TEXT))

        _run(external_api_clients.check_openphish("evil.example.com"))
        monkeypatch.setitem(external_api_clients._openphish_cache, "fetched_at", 0.0)
        _run(external_api_clients.check_openphish("evil.example.com"))

        assert len(fake.calls) == 2

    def test_raises_service_error_on_http_error(self, monkeypatch):
        _patch_client(monkeypatch, response=_response(503, "unavailable"))

        with pytest.raises(ServiceError):
            _run(external_api_clients.check_openphish("evil.example.com"))

    def test_raises_service_unavailable_on_connection_error(self, monkeypatch):
        _patch_client(
            monkeypatch,
            error=httpx.ConnectError("boom", request=httpx.Request("GET", "https://x")),
        )

        with pytest.raises(ServiceUnavailableError):
            _run(external_api_clients.check_openphish("evil.example.com"))
