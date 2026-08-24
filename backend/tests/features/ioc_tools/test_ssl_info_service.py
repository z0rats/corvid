"""resolve_validated_ip and the blocking _fetch_certificate_sync are both
monkeypatched directly (SSRF resolution itself is covered by
test_ssrf_guard.py; the real TLS handshake needs a live socket) so these
tests focus on perform_ssl_info_lookup's own logic: expiry/hostname-match
derivation and error mapping."""

import asyncio
import ssl
from datetime import UTC, datetime, timedelta

import pytest

from app.core.exceptions import AppHTTPException
from app.core.security.ssrf_guard import SSRFValidationError
from app.features.ioc_tools.domain_finder.schemas.domain_schemas import SslInfoRequest
from app.features.ioc_tools.domain_finder.service import ssl_info_service
from app.features.ioc_tools.domain_finder.service.ssl_info_service import (
    _hostname_matches,
    perform_ssl_info_lookup,
)


def _run(coro):
    return asyncio.run(coro)


def _raw_cert(**overrides) -> dict:
    now = datetime.now(UTC)
    base = {
        "subject": "CN=example.com",
        "issuer": "CN=Test CA",
        "serial_number": "1a2b3c",
        "not_before": now - timedelta(days=30),
        "not_after": now + timedelta(days=60),
        "subject_alt_names": ["example.com", "www.example.com"],
        "cipher": "TLS_AES_256_GCM_SHA384",
        "tls_version": "TLSv1.3",
    }
    base.update(overrides)
    return base


def _patch(monkeypatch, *, ip="93.184.216.34", cert=None, resolve_exc=None, fetch_exc=None):
    def fake_resolve(domain, *, allow_private=False):
        if resolve_exc:
            raise resolve_exc
        return ip

    async def fake_to_thread(func, domain, resolved_ip):
        if fetch_exc:
            raise fetch_exc
        return cert if cert is not None else _raw_cert()

    monkeypatch.setattr(ssl_info_service, "resolve_validated_ip", fake_resolve)
    monkeypatch.setattr(asyncio, "to_thread", fake_to_thread)


def test_hostname_matches_exact_and_wildcard_san():
    assert _hostname_matches("example.com", ["example.com"]) is True
    assert _hostname_matches("api.example.com", ["*.example.com"]) is True
    assert _hostname_matches("a.b.example.com", ["*.example.com"]) is False
    assert _hostname_matches("evil.com", ["example.com"]) is False


def test_hostname_matches_is_case_insensitive():
    assert _hostname_matches("Example.COM", ["example.com"]) is True


def test_perform_ssl_info_lookup_returns_parsed_certificate(monkeypatch):
    _patch(monkeypatch, cert=_raw_cert())

    result = _run(perform_ssl_info_lookup(SslInfoRequest(domain="example.com")))

    assert result.domain == "example.com"
    assert result.subject == "CN=example.com"
    assert result.issuer == "CN=Test CA"
    assert result.hostname_matches is True
    assert result.is_expired is False
    assert result.days_until_expiry > 0


def test_perform_ssl_info_lookup_flags_expired_certificate(monkeypatch):
    now = datetime.now(UTC)
    _patch(
        monkeypatch,
        cert=_raw_cert(not_before=now - timedelta(days=400), not_after=now - timedelta(days=10)),
    )

    result = _run(perform_ssl_info_lookup(SslInfoRequest(domain="example.com")))

    assert result.is_expired is True
    assert result.days_until_expiry < 0


def test_perform_ssl_info_lookup_flags_hostname_mismatch(monkeypatch):
    _patch(monkeypatch, cert=_raw_cert(subject_alt_names=["other-domain.example"]))

    result = _run(perform_ssl_info_lookup(SslInfoRequest(domain="example.com")))

    assert result.hostname_matches is False


def test_raises_400_on_ssrf_validation_failure(monkeypatch):
    _patch(monkeypatch, resolve_exc=SSRFValidationError("resolves to a private address"))

    with pytest.raises(AppHTTPException) as exc_info:
        _run(perform_ssl_info_lookup(SslInfoRequest(domain="internal.example")))

    assert exc_info.value.status_code == 400
    assert exc_info.value.error_code == "SSL_INFO_INVALID_HOST"


def test_raises_504_on_timeout(monkeypatch):
    _patch(monkeypatch, fetch_exc=TimeoutError("timed out"))

    with pytest.raises(AppHTTPException) as exc_info:
        _run(perform_ssl_info_lookup(SslInfoRequest(domain="example.com")))

    assert exc_info.value.status_code == 504
    assert exc_info.value.error_code == "SSL_INFO_TIMEOUT"


def test_raises_502_on_ssl_error(monkeypatch):
    _patch(monkeypatch, fetch_exc=ssl.SSLError("handshake failed"))

    with pytest.raises(AppHTTPException) as exc_info:
        _run(perform_ssl_info_lookup(SslInfoRequest(domain="example.com")))

    assert exc_info.value.status_code == 502
    assert exc_info.value.error_code == "SSL_INFO_CONNECTION_ERROR"


def test_raises_502_on_connection_refused(monkeypatch):
    _patch(monkeypatch, fetch_exc=ConnectionRefusedError("refused"))

    with pytest.raises(AppHTTPException) as exc_info:
        _run(perform_ssl_info_lookup(SslInfoRequest(domain="example.com")))

    assert exc_info.value.status_code == 502
    assert exc_info.value.error_code == "SSL_INFO_CONNECTION_ERROR"


def test_ssl_info_request_rejects_wildcard_patterns():
    with pytest.raises(ValueError):
        SslInfoRequest(domain="example-*")
