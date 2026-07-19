import asyncio

import pytest

from app.core.exceptions import AppHTTPException
from app.features.ioc_tools.domain_finder.schemas.domain_schemas import CtSubdomainsRequest
from app.features.ioc_tools.domain_finder.service import ct_subdomains_service
from app.features.ioc_tools.domain_finder.service.ct_subdomains_service import (
    _parse_crtsh_date,
    perform_ct_subdomains_lookup,
)

CRTSH_SAMPLE = [
    {
        "id": 1234567,
        "issuer_name": "C=US, O=Let's Encrypt, CN=R3",
        "common_name": "www.example.com",
        "name_value": "www.example.com\nexample.com",
        "not_before": "2024-01-15T00:00:00",
        "not_after": "2024-04-15T23:59:59",
    },
    {
        "id": 1234568,
        "issuer_name": "C=US, O=Let's Encrypt, CN=R3",
        "common_name": "*.dev.example.com",
        "name_value": "*.dev.example.com",
        "not_before": "2024-02-01T00:00:00",
        "not_after": "2024-05-01T23:59:59",
    },
    {
        # multi-SAN cert also covering an unrelated domain - shouldn't leak into results
        "id": 1234569,
        "issuer_name": "C=US, O=DigiCert Inc, CN=DigiCert TLS RSA SHA256 2020 CA1",
        "common_name": "api.example.com",
        "name_value": "api.example.com\nunrelated-domain.net",
        "not_before": "2024-03-01T00:00:00",
        "not_after": "2024-06-01T23:59:59",
    },
]


def test_parse_crtsh_date_parses_naive_iso8601():
    parsed = _parse_crtsh_date("2024-01-15T00:00:00")

    assert parsed is not None
    assert parsed.year == 2024 and parsed.month == 1 and parsed.day == 15


def test_parse_crtsh_date_returns_none_for_missing_or_invalid():
    assert _parse_crtsh_date(None) is None
    assert _parse_crtsh_date("not-a-date") is None


def test_perform_ct_subdomains_lookup_dedupes_and_filters_unrelated_names(monkeypatch):
    async def fake_fetch(domain):
        return CRTSH_SAMPLE

    monkeypatch.setattr(ct_subdomains_service, "fetch_crtsh_certificates", fake_fetch)

    result = asyncio.run(perform_ct_subdomains_lookup(CtSubdomainsRequest(domain="example.com")))

    assert result.domain == "example.com"
    assert result.subdomains == ["api.example.com", "dev.example.com", "example.com", "www.example.com"]
    assert "unrelated-domain.net" not in result.subdomains
    assert result.total_certificates == 3
    assert len(result.certificates) == 3


def test_perform_ct_subdomains_lookup_strips_wildcard_prefix(monkeypatch):
    async def fake_fetch(domain):
        return [CRTSH_SAMPLE[1]]

    monkeypatch.setattr(ct_subdomains_service, "fetch_crtsh_certificates", fake_fetch)

    result = asyncio.run(perform_ct_subdomains_lookup(CtSubdomainsRequest(domain="example.com")))

    assert result.subdomains == ["dev.example.com"]


def test_perform_ct_subdomains_lookup_handles_empty_response(monkeypatch):
    async def fake_fetch(domain):
        return []

    monkeypatch.setattr(ct_subdomains_service, "fetch_crtsh_certificates", fake_fetch)

    result = asyncio.run(perform_ct_subdomains_lookup(CtSubdomainsRequest(domain="doesnotexist.example")))

    assert result.subdomains == []
    assert result.total_certificates == 0


def test_perform_ct_subdomains_lookup_propagates_fetch_errors(monkeypatch):
    async def fake_fetch(domain):
        raise AppHTTPException(status_code=504, detail="timeout", error_code="CRTSH_TIMEOUT")

    monkeypatch.setattr(ct_subdomains_service, "fetch_crtsh_certificates", fake_fetch)

    with pytest.raises(AppHTTPException) as exc_info:
        asyncio.run(perform_ct_subdomains_lookup(CtSubdomainsRequest(domain="example.com")))

    assert exc_info.value.status_code == 504


def test_ct_subdomains_request_rejects_wildcard_patterns():
    with pytest.raises(ValueError):
        CtSubdomainsRequest(domain="example-*")


def test_ct_subdomains_request_normalizes_protocol_and_path():
    req = CtSubdomainsRequest(domain="HTTPS://Example.COM/path")

    assert req.domain == "example.com"
