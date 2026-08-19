import asyncio

import httpx
import pytest

from app.features.dork_runner.service.engines import base as engines_base


def _run(coro):
    return asyncio.run(coro)


@pytest.fixture(autouse=True)
def _no_real_retry_delay(monkeypatch):
    # fetch_html awaits a real RETRY_DELAY between attempts - replace it with a
    # no-op so a retry-exhaustion test doesn't actually wait.
    async def _instant_sleep(_seconds):
        return None

    monkeypatch.setattr(engines_base.asyncio, "sleep", _instant_sleep)


class TestFetchHtml:
    def test_returns_the_response_body_on_a_200(self, patch_httpx_transport):
        patch_httpx_transport(lambda request: httpx.Response(200, text="<html>ok</html>"))

        result = _run(engines_base.fetch_html("GET", "https://example.test/search"))

        assert result == "<html>ok</html>"

    def test_retries_once_on_a_non_200_status_then_succeeds(self, patch_httpx_transport):
        attempts = {"count": 0}

        def handler(request):
            attempts["count"] += 1
            if attempts["count"] == 1:
                return httpx.Response(429, text="rate limited")
            return httpx.Response(200, text="<html>ok on retry</html>")

        patch_httpx_transport(handler)

        result = _run(engines_base.fetch_html("GET", "https://example.test/search"))

        assert result == "<html>ok on retry</html>"
        assert attempts["count"] == 2

    def test_returns_none_once_retries_are_exhausted_on_repeated_non_200(
        self, patch_httpx_transport
    ):
        patch_httpx_transport(lambda request: httpx.Response(503, text="blocked"))

        result = _run(engines_base.fetch_html("GET", "https://example.test/search"))

        assert result is None

    def test_returns_none_once_retries_are_exhausted_on_a_connection_error(
        self, patch_httpx_transport
    ):
        def handler(request):
            raise httpx.ConnectError("connection refused", request=request)

        patch_httpx_transport(handler)

        result = _run(engines_base.fetch_html("GET", "https://example.test/search"))

        assert result is None

    def test_sends_the_given_method_params_and_data(self, patch_httpx_transport):
        captured = {}

        def handler(request):
            captured["method"] = request.method
            captured["query"] = dict(request.url.params)
            captured["body"] = request.content
            return httpx.Response(200, text="ok")

        patch_httpx_transport(handler)

        _run(
            engines_base.fetch_html(
                "POST", "https://example.test/search", params={"q": "site:example.com"}
            )
        )

        assert captured["method"] == "POST"
        assert captured["query"] == {"q": "site:example.com"}
