"""`provider_http` - the one seam every domain_finder provider panel's request goes through.
Its error mapping is tested here once; each provider's own tests cover only its parsing and
provider-specific statuses (quota hit, rejected key, not found)."""

import asyncio

import httpx
import pytest

from app.core.exceptions import AppHTTPException
from app.features.ioc_tools.domain_finder.service.provider_http import (
    USER_AGENT,
    Provider,
    provider_errors,
    provider_get,
)

EXAMPLE = Provider(name="Example", code="EXAMPLE", base_url="https://api.example.test/v1")


def _run(coro):
    return asyncio.run(coro)


def _get(**kwargs):
    kwargs.setdefault("parse", lambda response: response.json())
    return _run(provider_get(EXAMPLE, "/lookup", subject="example.com", **kwargs))


def test_requests_the_fixed_base_url_with_default_and_extra_headers(patch_httpx_transport):
    seen = {}

    def handler(request):
        seen.update(url=str(request.url), headers=request.headers)
        return httpx.Response(200, json={"ok": True})

    patch_httpx_transport(handler)

    assert _get(params={"q": "x"}, headers={"X-API-Key": "k"}) == {"ok": True}
    assert seen["url"] == "https://api.example.test/v1/lookup?q=x"
    assert seen["headers"]["user-agent"] == USER_AGENT
    assert seen["headers"]["accept"] == "application/json"
    assert seen["headers"]["x-api-key"] == "k"


@pytest.mark.parametrize(
    ("handler", "parse", "status", "suffix"),
    [
        (
            lambda r: (_ for _ in ()).throw(httpx.ReadTimeout("slow", request=r)),
            None,
            504,
            "TIMEOUT",
        ),
        (
            lambda r: (_ for _ in ()).throw(httpx.ConnectError("refused", request=r)),
            None,
            503,
            "CONNECTION_ERROR",
        ),
        (lambda r: httpx.Response(418), None, 418, "API_ERROR"),
        (lambda r: httpx.Response(200, text="<html>busy</html>"), None, 502, "INVALID_RESPONSE"),
        (lambda r: httpx.Response(200, json={}), lambda r: {}["missing"], 500, "UNEXPECTED_ERROR"),
    ],
    ids=["timeout", "connect", "http-status", "unparseable", "unexpected"],
)
def test_maps_every_failure_onto_the_providers_error_codes(
    patch_httpx_transport, handler, parse, status, suffix
):
    patch_httpx_transport(handler)

    with pytest.raises(AppHTTPException) as exc_info:
        _get(**({"parse": parse} if parse else {}))

    assert exc_info.value.status_code == status
    assert exc_info.value.error_code == f"EXAMPLE_{suffix}"


def test_a_check_raising_its_own_error_runs_before_the_status_check(patch_httpx_transport):
    patch_httpx_transport(lambda request: httpx.Response(401))

    def check(response):
        if response.status_code == 401:
            raise EXAMPLE.error(401, "INVALID_KEY", "bad key")

    with pytest.raises(AppHTTPException) as exc_info:
        _get(check=check)

    assert exc_info.value.error_code == "EXAMPLE_INVALID_KEY"


def test_provider_errors_passes_an_apphttpexception_through_unchanged():
    async def scenario():
        async with provider_errors(EXAMPLE, "example.com"):
            raise EXAMPLE.error(404, "NOT_FOUND", "nothing")

    with pytest.raises(AppHTTPException) as exc_info:
        _run(scenario())

    assert (exc_info.value.status_code, exc_info.value.error_code) == (404, "EXAMPLE_NOT_FOUND")
