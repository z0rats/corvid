"""safe_get is monkeypatched directly (rather than exercised through real DNS
resolution/SSRF checks, already covered by test_ssrf_guard.py) so these tests
focus on fetch_rdap_domain_data's own logic: 404 handling, recovering the
answering RDAP server from the pinned request's Host header, and error mapping."""

import asyncio

import httpx
import pytest

from app.core.exceptions import AppHTTPException
from app.features.ioc_tools.domain_finder.service import rdap_api_service
from app.features.ioc_tools.domain_finder.service.rdap_api_service import fetch_rdap_domain_data


def _run(coro):
    return asyncio.run(coro)


def _response(status_code: int, *, json=None, host="rdap.verisign.com") -> httpx.Response:
    request = httpx.Request("GET", "https://rdap.org/domain/example.com", headers={"host": host})
    kwargs = {}
    if json is not None:
        kwargs["json"] = json
    return httpx.Response(status_code, request=request, **kwargs)


def _patch_safe_get(monkeypatch, result=None, exc=None):
    async def fake_safe_get(client, url, **kwargs):
        if exc:
            raise exc
        return result

    monkeypatch.setattr(rdap_api_service, "safe_get", fake_safe_get)


def test_returns_data_and_answering_server_on_success(monkeypatch):
    _patch_safe_get(
        monkeypatch,
        result=_response(200, json={"ldhName": "EXAMPLE.COM"}, host="rdap.verisign.com"),
    )

    data, server = _run(fetch_rdap_domain_data("example.com"))

    assert data == {"ldhName": "EXAMPLE.COM"}
    assert server == "rdap.verisign.com"


def test_raises_404_for_domain_not_found(monkeypatch):
    _patch_safe_get(monkeypatch, result=_response(404))

    with pytest.raises(AppHTTPException) as exc_info:
        _run(fetch_rdap_domain_data("doesnotexist.example"))

    assert exc_info.value.status_code == 404
    assert exc_info.value.error_code == "RDAP_NOT_FOUND"


def test_raises_with_upstream_status_on_other_http_errors(monkeypatch):
    _patch_safe_get(monkeypatch, result=_response(500))

    with pytest.raises(AppHTTPException) as exc_info:
        _run(fetch_rdap_domain_data("example.com"))

    assert exc_info.value.status_code == 500
    assert exc_info.value.error_code == "RDAP_API_ERROR"


def test_raises_504_on_timeout(monkeypatch):
    _patch_safe_get(monkeypatch, exc=httpx.TimeoutException("timed out"))

    with pytest.raises(AppHTTPException) as exc_info:
        _run(fetch_rdap_domain_data("example.com"))

    assert exc_info.value.status_code == 504
    assert exc_info.value.error_code == "RDAP_TIMEOUT"


def test_raises_503_on_connection_error(monkeypatch):
    _patch_safe_get(monkeypatch, exc=httpx.ConnectError("refused"))

    with pytest.raises(AppHTTPException) as exc_info:
        _run(fetch_rdap_domain_data("example.com"))

    assert exc_info.value.status_code == 503
    assert exc_info.value.error_code == "RDAP_CONNECTION_ERROR"


def test_missing_host_header_falls_back_to_unknown(monkeypatch):
    response = _response(200, json={})
    del response.request.headers["host"]
    _patch_safe_get(monkeypatch, result=response)

    _, server = _run(fetch_rdap_domain_data("example.com"))

    assert server == "unknown"
