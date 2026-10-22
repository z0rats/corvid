import asyncio

import httpx
import pytest

from app.features.telegram_search.service.tme_client import (
    TelegramRateLimitedError,
    TelegramSourceError,
    TmeClient,
)


def _fetch(handler, method: str, *args, **kwargs):
    async def go():
        async with TmeClient(transport=httpx.MockTransport(handler)) as client:
            return await getattr(client, method)(*args, **kwargs)

    return asyncio.run(go())


def test_preview_page_requests_the_s_path_with_the_before_cursor():
    seen = []

    def handler(request):
        seen.append(str(request.url))
        return httpx.Response(200, text="<html>page</html>")

    assert _fetch(handler, "fetch_preview_page", "durov", before=300) == "<html>page</html>"
    assert _fetch(handler, "fetch_preview_page", "durov") == "<html>page</html>"
    assert seen == ["https://t.me/s/durov?before=300", "https://t.me/s/durov"]


def test_preview_redirect_means_no_preview():
    def handler(request):
        return httpx.Response(302, headers={"Location": "https://t.me/python"})

    assert _fetch(handler, "fetch_preview_page", "python") is None


def test_profile_page_redirect_is_a_source_error():
    def handler(request):
        return httpx.Response(302, headers={"Location": "https://telegram.org"})

    with pytest.raises(TelegramSourceError, match="redirected"):
        _fetch(handler, "fetch_profile_page", "durov")


def test_429_maps_to_rate_limited_with_retry_after():
    def handler(request):
        return httpx.Response(429, headers={"Retry-After": "42"})

    with pytest.raises(TelegramRateLimitedError, match="retry in 42 s") as exc_info:
        _fetch(handler, "fetch_profile_page", "durov")
    assert exc_info.value.retry_after == 42


def test_429_without_retry_after_uses_the_default_wait():
    def handler(request):
        return httpx.Response(429)

    with pytest.raises(TelegramRateLimitedError, match="retry in 60 s"):
        _fetch(handler, "fetch_profile_page", "durov")


def test_server_error_is_a_source_error():
    def handler(request):
        return httpx.Response(503)

    with pytest.raises(TelegramSourceError, match="HTTP 503"):
        _fetch(handler, "fetch_profile_page", "durov")


def test_network_error_is_a_source_error_keeping_the_cause():
    def handler(request):
        raise httpx.ConnectError("boom")

    with pytest.raises(TelegramSourceError, match="unreachable") as exc_info:
        _fetch(handler, "fetch_profile_page", "durov")
    assert isinstance(exc_info.value.__cause__, httpx.ConnectError)
