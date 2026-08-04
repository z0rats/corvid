"""Uses httpx.MockTransport (stdlib to httpx, no extra dependency) rather than
mocking away httpx.AsyncClient's behavior, so raise_for_status()/response.json()
parsing in fetch_crtsh_certificates runs for real against a canned response."""
import asyncio

import httpx
import pytest

from app.core.exceptions import AppHTTPException
from app.features.ioc_tools.domain_finder.service.crtsh_api_service import fetch_crtsh_certificates


def _run(coro):
    return asyncio.run(coro)


def _patch_transport(monkeypatch, handler):
    real_async_client = httpx.AsyncClient

    def factory(*args, **kwargs):
        kwargs["transport"] = httpx.MockTransport(handler)
        return real_async_client(*args, **kwargs)

    monkeypatch.setattr(httpx, "AsyncClient", factory)


def test_returns_parsed_certificate_list_on_success(monkeypatch):
    certs = [{"id": 1, "name_value": "www.example.com"}, {"id": 2, "name_value": "mail.example.com"}]

    def handler(request):
        assert request.url.params["q"] == "%.example.com"
        return httpx.Response(200, json=certs)

    _patch_transport(monkeypatch, handler)

    result = _run(fetch_crtsh_certificates("example.com"))

    assert result == certs


def test_returns_empty_list_for_empty_response_body(monkeypatch):
    _patch_transport(monkeypatch, lambda request: httpx.Response(200, content=b""))

    assert _run(fetch_crtsh_certificates("example.com")) == []


def test_raises_502_when_response_is_not_valid_json(monkeypatch):
    _patch_transport(monkeypatch, lambda request: httpx.Response(200, text="<html>overloaded</html>"))

    with pytest.raises(AppHTTPException) as exc_info:
        _run(fetch_crtsh_certificates("example.com"))

    assert exc_info.value.status_code == 502
    assert exc_info.value.error_code == "CRTSH_INVALID_RESPONSE"


def test_raises_with_upstream_status_code_on_http_error(monkeypatch):
    _patch_transport(monkeypatch, lambda request: httpx.Response(500, text="server error"))

    with pytest.raises(AppHTTPException) as exc_info:
        _run(fetch_crtsh_certificates("example.com"))

    assert exc_info.value.status_code == 500
    assert exc_info.value.error_code == "CRTSH_API_ERROR"


def test_raises_504_on_timeout(monkeypatch):
    def handler(request):
        raise httpx.TimeoutException("timed out", request=request)

    _patch_transport(monkeypatch, handler)

    with pytest.raises(AppHTTPException) as exc_info:
        _run(fetch_crtsh_certificates("example.com"))

    assert exc_info.value.status_code == 504
    assert exc_info.value.error_code == "CRTSH_TIMEOUT"


def test_raises_503_on_connection_error(monkeypatch):
    def handler(request):
        raise httpx.ConnectError("connection refused", request=request)

    _patch_transport(monkeypatch, handler)

    with pytest.raises(AppHTTPException) as exc_info:
        _run(fetch_crtsh_certificates("example.com"))

    assert exc_info.value.status_code == 503
    assert exc_info.value.error_code == "CRTSH_CONNECTION_ERROR"
