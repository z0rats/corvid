import asyncio

import httpx
import pytest

from app.features.phone_search.service.checkers import facebook_checker

_IDENTIFY_FORM_HTML = """
<html><body>
<form action="https://www.facebook.com/login/identify/submit">
  <input type="hidden" name="fb_dtsg" value="dtsg123">
  <input type="text" id="identify_email" name="email" value="">
</form>
</body></html>
"""


def _run(coro):
    return asyncio.run(coro)


class TestCheck:
    def test_returns_true_when_the_not_found_marker_is_absent(self):
        async def handler(request: httpx.Request) -> httpx.Response:
            if request.method == "GET":
                return httpx.Response(200, text=_IDENTIFY_FORM_HTML)
            return httpx.Response(200, text="<html>Is this you? <div>Account found</div></html>")

        async def _scenario():
            async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
                return await facebook_checker.check("+15551234567", client, 5)

        assert _run(_scenario()) is True

    def test_returns_false_when_the_not_found_marker_is_present(self):
        async def handler(request: httpx.Request) -> httpx.Response:
            if request.method == "GET":
                return httpx.Response(200, text=_IDENTIFY_FORM_HTML)
            return httpx.Response(200, text="<html>No search results</html>")

        async def _scenario():
            async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
                return await facebook_checker.check("+15551234567", client, 5)

        assert _run(_scenario()) is False

    def test_submits_the_phone_number_under_the_identify_email_fields_name(self):
        captured = {}

        async def handler(request: httpx.Request) -> httpx.Response:
            if request.method == "GET":
                return httpx.Response(200, text=_IDENTIFY_FORM_HTML)
            captured["body"] = request.content
            return httpx.Response(200, text="<html>No search results</html>")

        async def _scenario():
            async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
                await facebook_checker.check("+15551234567", client, 5)

        _run(_scenario())
        assert b"email=%2B15551234567" in captured["body"]
        assert b"fb_dtsg=dtsg123" in captured["body"]

    def test_raises_when_no_form_is_found_on_the_identify_page(self):
        async def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(200, text="<html><body>no form here</body></html>")

        async def _scenario():
            async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
                await facebook_checker.check("+15551234567", client, 5)

        with pytest.raises(ValueError, match="identify form not found"):
            _run(_scenario())
