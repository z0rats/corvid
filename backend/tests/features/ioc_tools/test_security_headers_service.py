"""safe_get is monkeypatched directly (rather than exercised through real DNS
resolution/SSRF checks, already covered by test_ssrf_guard.py) so these tests
focus on perform_security_headers_lookup's own logic: header presence/absence
classification, HSTS directive parsing, and error mapping."""

import asyncio

import httpx
import pytest

from app.core.exceptions import AppHTTPException
from app.core.security.ssrf_guard import SSRFValidationError
from app.features.ioc_tools.domain_finder.schemas.domain_schemas import SecurityHeadersRequest
from app.features.ioc_tools.domain_finder.service import security_headers_service
from app.features.ioc_tools.domain_finder.service.security_headers_service import (
    perform_security_headers_lookup,
)


def _run(coro):
    return asyncio.run(coro)


def _response(status_code: int, headers: dict[str, str]) -> httpx.Response:
    request = httpx.Request("GET", "https://example.com/")
    return httpx.Response(status_code, headers=headers, request=request)


def _patch_safe_get(monkeypatch, result=None, exc=None):
    async def fake_safe_get(client, url, **kwargs):
        if exc:
            raise exc
        return result

    monkeypatch.setattr(security_headers_service, "safe_get", fake_safe_get)


def test_classifies_present_and_missing_headers(monkeypatch):
    _patch_safe_get(
        monkeypatch,
        result=_response(
            200,
            {
                "strict-transport-security": "max-age=31536000; includeSubDomains; preload",
                "x-frame-options": "DENY",
            },
        ),
    )

    result = _run(perform_security_headers_lookup(SecurityHeadersRequest(domain="example.com")))

    assert result.present_headers["Strict-Transport-Security"] == (
        "max-age=31536000; includeSubDomains; preload"
    )
    assert result.present_headers["X-Frame-Options"] == "DENY"
    assert "Content-Security-Policy" in result.missing_headers
    assert "X-Frame-Options" not in result.missing_headers


def test_parses_hsts_directives(monkeypatch):
    _patch_safe_get(
        monkeypatch,
        result=_response(200, {"strict-transport-security": "max-age=63072000; includeSubDomains"}),
    )

    result = _run(perform_security_headers_lookup(SecurityHeadersRequest(domain="example.com")))

    assert result.hsts.max_age == 63072000
    assert result.hsts.include_subdomains is True
    assert result.hsts.preload is False


def test_hsts_is_none_when_header_absent(monkeypatch):
    _patch_safe_get(monkeypatch, result=_response(200, {}))

    result = _run(perform_security_headers_lookup(SecurityHeadersRequest(domain="example.com")))

    assert result.hsts is None
    assert result.missing_headers  # every header missing


def test_hsts_survives_an_unparseable_max_age(monkeypatch):
    _patch_safe_get(
        monkeypatch, result=_response(200, {"strict-transport-security": "max-age=notanumber"})
    )

    result = _run(perform_security_headers_lookup(SecurityHeadersRequest(domain="example.com")))

    assert result.hsts.max_age is None
    assert result.hsts.raw_value == "max-age=notanumber"


def test_raises_400_on_ssrf_validation_failure(monkeypatch):
    _patch_safe_get(monkeypatch, exc=SSRFValidationError("resolves to a private address"))

    with pytest.raises(AppHTTPException) as exc_info:
        _run(perform_security_headers_lookup(SecurityHeadersRequest(domain="internal.example")))

    assert exc_info.value.status_code == 400
    assert exc_info.value.error_code == "SECURITY_HEADERS_INVALID_HOST"


def test_raises_504_on_timeout(monkeypatch):
    _patch_safe_get(monkeypatch, exc=httpx.TimeoutException("timed out"))

    with pytest.raises(AppHTTPException) as exc_info:
        _run(perform_security_headers_lookup(SecurityHeadersRequest(domain="example.com")))

    assert exc_info.value.status_code == 504
    assert exc_info.value.error_code == "SECURITY_HEADERS_TIMEOUT"


def test_raises_503_on_connection_error(monkeypatch):
    _patch_safe_get(monkeypatch, exc=httpx.ConnectError("refused"))

    with pytest.raises(AppHTTPException) as exc_info:
        _run(perform_security_headers_lookup(SecurityHeadersRequest(domain="example.com")))

    assert exc_info.value.status_code == 503
    assert exc_info.value.error_code == "SECURITY_HEADERS_CONNECTION_ERROR"


def test_security_headers_request_rejects_wildcard_patterns():
    with pytest.raises(ValueError):
        SecurityHeadersRequest(domain="example-*")
