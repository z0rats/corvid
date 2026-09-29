import asyncio

import httpx
import pytest

from app.features.phone_search.service.checkers import microsoft_checker


def _run(coro):
    return asyncio.run(coro)


class TestCheck:
    def test_returns_true_when_credential_type_reports_an_existing_account(self):
        async def handler(request: httpx.Request) -> httpx.Response:
            if request.url.path.endswith("GetCredentialType.srf"):
                return httpx.Response(200, json={"IfExistsResult": 0})
            return httpx.Response(200, text='<script>var Config={"apiCanary":"abc123"};</script>')

        async def _scenario():
            async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
                return await microsoft_checker.check("+15551234567", client, 5)

        assert _run(_scenario()) is True

    def test_returns_false_when_credential_type_reports_no_account(self):
        async def handler(request: httpx.Request) -> httpx.Response:
            if request.url.path.endswith("GetCredentialType.srf"):
                return httpx.Response(200, json={"IfExistsResult": 1})
            return httpx.Response(200, text="<html></html>")

        async def _scenario():
            async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
                return await microsoft_checker.check("+15551234567", client, 5)

        assert _run(_scenario()) is False

    def test_forwards_the_canary_header_extracted_from_the_login_page(self):
        captured = {}

        async def handler(request: httpx.Request) -> httpx.Response:
            if request.url.path.endswith("GetCredentialType.srf"):
                captured["canary"] = request.headers.get("canary")
                return httpx.Response(200, json={"IfExistsResult": 1})
            return httpx.Response(
                200, text='<script>var Config={"apiCanary":"the-canary"};</script>'
            )

        async def _scenario():
            async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
                await microsoft_checker.check("+15551234567", client, 5)

        _run(_scenario())
        assert captured["canary"] == "the-canary"

    def test_still_posts_without_a_canary_header_when_none_is_found_on_the_login_page(self):
        captured = {}

        async def handler(request: httpx.Request) -> httpx.Response:
            if request.url.path.endswith("GetCredentialType.srf"):
                captured["canary"] = request.headers.get("canary")
                return httpx.Response(200, json={"IfExistsResult": 1})
            return httpx.Response(200, text="<html>no canary here</html>")

        async def _scenario():
            async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
                await microsoft_checker.check("+15551234567", client, 5)

        _run(_scenario())
        assert captured["canary"] is None

    def test_raises_on_a_non_2xx_login_page_response(self):
        async def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(503, text="blocked")

        async def _scenario():
            async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
                await microsoft_checker.check("+15551234567", client, 5)

        with pytest.raises(httpx.HTTPStatusError):
            _run(_scenario())
