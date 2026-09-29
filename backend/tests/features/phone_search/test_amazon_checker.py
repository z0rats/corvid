import asyncio

import httpx
import pytest

from app.features.phone_search.service.checkers import amazon_checker

_SIGNIN_FORM_HTML = """
<html><body>
<form name="signIn" action="https://www.amazon.com/ap/signin/next">
  <input type="hidden" name="appActionToken" value="tok123">
  <input type="text" name="email" value="">
</form>
</body></html>
"""


def _run(coro):
    return asyncio.run(coro)


class TestCheck:
    def test_returns_true_when_the_new_account_marker_is_absent(self):
        async def handler(request: httpx.Request) -> httpx.Response:
            if request.method == "GET":
                return httpx.Response(200, text=_SIGNIN_FORM_HTML)
            return httpx.Response(200, text="<html>Amazon Sign-In: enter your password</html>")

        async def _scenario():
            async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
                return await amazon_checker.check("+15551234567", client, 5)

        assert _run(_scenario()) is True

    def test_returns_false_when_the_new_account_marker_is_present(self):
        async def handler(request: httpx.Request) -> httpx.Response:
            if request.method == "GET":
                return httpx.Response(200, text=_SIGNIN_FORM_HTML)
            return httpx.Response(200, text="<html>Looks like you're New to Amazon</html>")

        async def _scenario():
            async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
                return await amazon_checker.check("+15551234567", client, 5)

        assert _run(_scenario()) is False

    def test_submits_the_phone_number_as_the_email_field_alongside_hidden_inputs(self):
        captured = {}

        async def handler(request: httpx.Request) -> httpx.Response:
            if request.method == "GET":
                return httpx.Response(200, text=_SIGNIN_FORM_HTML)
            captured["body"] = request.content
            return httpx.Response(200, text="<html>Amazon Sign-In</html>")

        async def _scenario():
            async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
                await amazon_checker.check("+15551234567", client, 5)

        _run(_scenario())
        assert b"email=%2B15551234567" in captured["body"]
        assert b"appActionToken=tok123" in captured["body"]

    def test_raises_when_no_form_is_found_on_the_signin_page(self):
        async def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(200, text="<html><body>no form here</body></html>")

        async def _scenario():
            async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
                await amazon_checker.check("+15551234567", client, 5)

        with pytest.raises(ValueError, match="sign-in form not found"):
            _run(_scenario())
