import asyncio

import pytest

from app.core.exceptions import AppHTTPException
from app.features.ioc_tools.domain_finder.schemas.domain_schemas import CtSubdomainsRequest
from app.features.ioc_tools.domain_finder.service import ct_subdomains_service
from app.features.ioc_tools.domain_finder.service.certspotter_api_service import CertSpotterPage
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

CERTSPOTTER_PAGE = CertSpotterPage(
    issuances=[
        {"id": "1", "dns_names": ["example.com", "*.mail.example.com", "example.org"]},
        {"id": "2", "dns_names": ["MAIL.example.com"]},
    ],
    truncated=True,
)


def test_parse_crtsh_date_parses_naive_iso8601():
    parsed = _parse_crtsh_date("2024-01-15T00:00:00")

    assert parsed is not None
    assert parsed.year == 2024 and parsed.month == 1 and parsed.day == 15


def test_parse_crtsh_date_returns_none_for_missing_or_invalid():
    assert _parse_crtsh_date(None) is None
    assert _parse_crtsh_date("not-a-date") is None


def _serve(monkeypatch, crtsh=None, certspotter=None):
    """Stub both CT sources (empty by default); an exception value is raised instead."""

    def fake(value):
        async def fetch(domain):
            if isinstance(value, BaseException):
                raise value
            return value

        return fetch

    crtsh = [] if crtsh is None else crtsh
    certspotter = CertSpotterPage(issuances=[]) if certspotter is None else certspotter
    monkeypatch.setattr(ct_subdomains_service, "fetch_crtsh_certificates", fake(crtsh))
    monkeypatch.setattr(ct_subdomains_service, "fetch_certspotter_issuances", fake(certspotter))


def _lookup(domain="example.com"):
    return asyncio.run(perform_ct_subdomains_lookup(CtSubdomainsRequest(domain=domain)))


def _error(code, status=504):
    return AppHTTPException(status_code=status, detail=f"{code} detail", error_code=code)


def test_perform_ct_subdomains_lookup_dedupes_and_filters_unrelated_names(monkeypatch):
    _serve(monkeypatch, crtsh=CRTSH_SAMPLE)

    result = _lookup()

    assert result.domain == "example.com"
    assert result.subdomains == [
        "api.example.com",
        "dev.example.com",
        "example.com",
        "www.example.com",
    ]
    assert "unrelated-domain.net" not in result.subdomains
    assert result.total_certificates == 3
    assert len(result.certificates) == 3


def test_perform_ct_subdomains_lookup_strips_wildcard_prefix(monkeypatch):
    _serve(monkeypatch, crtsh=[CRTSH_SAMPLE[1]])

    assert _lookup().subdomains == ["dev.example.com"]


def test_perform_ct_subdomains_lookup_handles_empty_response(monkeypatch):
    _serve(monkeypatch)

    result = _lookup("doesnotexist.example")

    assert result.subdomains == []
    assert result.total_certificates == 0
    assert [(s.name, s.ok, s.subdomain_count) for s in result.sources] == [
        ("crt.sh", True, 0),
        ("Cert Spotter", True, 0),
    ]


def test_merges_both_sources_and_counts_each(monkeypatch):
    _serve(monkeypatch, crtsh=CRTSH_SAMPLE, certspotter=CERTSPOTTER_PAGE)

    result = _lookup()

    assert result.subdomains == [
        "api.example.com",
        "dev.example.com",
        "example.com",
        "mail.example.com",
        "www.example.com",
    ]
    crtsh, certspotter = result.sources
    assert (crtsh.name, crtsh.ok, crtsh.subdomain_count, crtsh.certificate_count) == (
        "crt.sh",
        True,
        4,
        3,
    )
    assert (certspotter.name, certspotter.subdomain_count, certspotter.certificate_count) == (
        "Cert Spotter",
        2,
        2,
    )
    assert certspotter.truncated is True
    # The per-certificate detail stays crt.sh-only.
    assert result.total_certificates == 3


def test_crtsh_down_still_returns_cert_spotter_subdomains(monkeypatch):
    _serve(monkeypatch, crtsh=_error("CRTSH_TIMEOUT"), certspotter=CERTSPOTTER_PAGE)

    result = _lookup()

    assert result.subdomains == ["example.com", "mail.example.com"]
    crtsh, certspotter = result.sources
    assert crtsh.ok is False
    assert crtsh.error_code == "CRTSH_TIMEOUT"
    assert crtsh.error == "CRTSH_TIMEOUT detail"
    assert certspotter.ok is True
    assert result.certificates == []


def test_cert_spotter_down_still_returns_crtsh_subdomains(monkeypatch):
    _serve(
        monkeypatch,
        crtsh=CRTSH_SAMPLE,
        certspotter=_error("CERTSPOTTER_RATE_LIMITED", status=429),
    )

    result = _lookup()

    assert len(result.subdomains) == 4
    assert result.sources[1].ok is False
    assert result.sources[1].error_code == "CERTSPOTTER_RATE_LIMITED"


def test_both_sources_down_fails_the_lookup_naming_both(monkeypatch):
    _serve(
        monkeypatch,
        crtsh=_error("CRTSH_TIMEOUT"),
        certspotter=_error("CERTSPOTTER_SCHEMA_DRIFT", status=502),
    )

    with pytest.raises(AppHTTPException) as exc_info:
        _lookup()

    assert exc_info.value.status_code == 502
    assert exc_info.value.error_code == "CT_ALL_SOURCES_FAILED"
    assert "crt.sh: CRTSH_TIMEOUT detail" in exc_info.value.detail
    assert "Cert Spotter: CERTSPOTTER_SCHEMA_DRIFT detail" in exc_info.value.detail
    # Each source's own code survives into the combined error.
    assert "(CRTSH_TIMEOUT)" in exc_info.value.detail
    assert "(CERTSPOTTER_SCHEMA_DRIFT)" in exc_info.value.detail


def test_an_unexpected_exception_is_not_swallowed_as_a_failed_source(monkeypatch):
    _serve(monkeypatch, crtsh=RuntimeError("bug"))

    with pytest.raises(RuntimeError, match="bug"):
        _lookup()


def test_ct_subdomains_request_rejects_wildcard_patterns():
    with pytest.raises(ValueError):
        CtSubdomainsRequest(domain="example-*")


def test_ct_subdomains_request_normalizes_protocol_and_path():
    req = CtSubdomainsRequest(domain="HTTPS://Example.COM/path")

    assert req.domain == "example.com"
