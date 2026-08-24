"""Uses httpx.MockTransport (stdlib to httpx, no extra dependency) rather than
mocking away httpx.AsyncClient's behavior, so raise_for_status()/text parsing
in fetch_hackertarget_hosts runs for real against a canned response."""

import asyncio

import httpx
import pytest

from app.core.exceptions import AppHTTPException
from app.features.ioc_tools.domain_finder.service.hackertarget_api_service import (
    fetch_hackertarget_hosts,
)


def _run(coro):
    return asyncio.run(coro)


def test_returns_parsed_host_list_on_success(patch_httpx_transport):
    def handler(request):
        assert request.url.params["q"] == "example.com"
        return httpx.Response(
            200, text="www.example.com,93.184.216.34\nmail.example.com,93.184.216.35\n"
        )

    patch_httpx_transport(handler)

    result = _run(fetch_hackertarget_hosts("example.com"))

    assert result == [
        ("www.example.com", "93.184.216.34"),
        ("mail.example.com", "93.184.216.35"),
    ]


def test_returns_empty_list_for_empty_response_body(patch_httpx_transport):
    patch_httpx_transport(lambda request: httpx.Response(200, content=b""))

    assert _run(fetch_hackertarget_hosts("example.com")) == []


def test_returns_empty_list_for_error_body(patch_httpx_transport):
    patch_httpx_transport(lambda request: httpx.Response(200, text="error invalid host"))

    assert _run(fetch_hackertarget_hosts("doesnotexist.example")) == []


def test_raises_429_when_free_tier_quota_exceeded(patch_httpx_transport):
    patch_httpx_transport(
        lambda request: httpx.Response(
            200,
            text="error API count exceeded, upgrade to Membership: "
            "https://hackertarget.com/membership/",
        )
    )

    with pytest.raises(AppHTTPException) as exc_info:
        _run(fetch_hackertarget_hosts("example.com"))

    assert exc_info.value.status_code == 429
    assert exc_info.value.error_code == "HACKERTARGET_RATE_LIMITED"


def test_omits_ip_when_line_has_no_comma(patch_httpx_transport):
    patch_httpx_transport(lambda request: httpx.Response(200, text="www.example.com\n"))

    assert _run(fetch_hackertarget_hosts("example.com")) == [("www.example.com", None)]


def test_raises_with_upstream_status_code_on_http_error(patch_httpx_transport):
    patch_httpx_transport(lambda request: httpx.Response(500, text="server error"))

    with pytest.raises(AppHTTPException) as exc_info:
        _run(fetch_hackertarget_hosts("example.com"))

    assert exc_info.value.status_code == 500
    assert exc_info.value.error_code == "HACKERTARGET_API_ERROR"


def test_raises_504_on_timeout(patch_httpx_transport):
    def handler(request):
        raise httpx.TimeoutException("timed out", request=request)

    patch_httpx_transport(handler)

    with pytest.raises(AppHTTPException) as exc_info:
        _run(fetch_hackertarget_hosts("example.com"))

    assert exc_info.value.status_code == 504
    assert exc_info.value.error_code == "HACKERTARGET_TIMEOUT"


def test_raises_503_on_connection_error(patch_httpx_transport):
    def handler(request):
        raise httpx.ConnectError("connection refused", request=request)

    patch_httpx_transport(handler)

    with pytest.raises(AppHTTPException) as exc_info:
        _run(fetch_hackertarget_hosts("example.com"))

    assert exc_info.value.status_code == 503
    assert exc_info.value.error_code == "HACKERTARGET_CONNECTION_ERROR"
