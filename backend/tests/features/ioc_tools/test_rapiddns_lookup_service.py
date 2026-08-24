import asyncio

import pytest

from app.core.exceptions import AppHTTPException
from app.features.ioc_tools.domain_finder.schemas.domain_schemas import (
    RapidDnsSubdomainsRequest,
)
from app.features.ioc_tools.domain_finder.service import rapiddns_lookup_service
from app.features.ioc_tools.domain_finder.service.rapiddns_lookup_service import (
    perform_rapiddns_lookup,
)


def test_perform_rapiddns_lookup_dedupes_and_sorts_subdomains(monkeypatch):
    async def fake_fetch(domain):
        return [
            ("www.example.com", "A", "1.1.1.1"),
            ("api.example.com", "AAAA", "::1"),
            ("www.example.com", "A", "1.1.1.1"),
        ]

    monkeypatch.setattr(rapiddns_lookup_service, "fetch_rapiddns_records", fake_fetch)

    result = asyncio.run(perform_rapiddns_lookup(RapidDnsSubdomainsRequest(domain="example.com")))

    assert result.domain == "example.com"
    assert result.subdomains == ["api.example.com", "www.example.com"]
    assert result.total_records == 3


def test_perform_rapiddns_lookup_excludes_unrelated_hosts_from_subdomains(monkeypatch):
    async def fake_fetch(domain):
        return [("www.example.com", "A", "1.1.1.1"), ("unrelated-host.net", "A", "3.3.3.3")]

    monkeypatch.setattr(rapiddns_lookup_service, "fetch_rapiddns_records", fake_fetch)

    result = asyncio.run(perform_rapiddns_lookup(RapidDnsSubdomainsRequest(domain="example.com")))

    assert result.subdomains == ["www.example.com"]
    # Still surfaced in the raw record list, just not counted as a subdomain
    assert len(result.records) == 2


def test_perform_rapiddns_lookup_handles_empty_response(monkeypatch):
    async def fake_fetch(domain):
        return []

    monkeypatch.setattr(rapiddns_lookup_service, "fetch_rapiddns_records", fake_fetch)

    result = asyncio.run(
        perform_rapiddns_lookup(RapidDnsSubdomainsRequest(domain="doesnotexist.example"))
    )

    assert result.subdomains == []
    assert result.total_records == 0


def test_perform_rapiddns_lookup_propagates_fetch_errors(monkeypatch):
    async def fake_fetch(domain):
        raise AppHTTPException(
            status_code=502, detail="bad gateway", error_code="RAPIDDNS_API_ERROR"
        )

    monkeypatch.setattr(rapiddns_lookup_service, "fetch_rapiddns_records", fake_fetch)

    with pytest.raises(AppHTTPException) as exc_info:
        asyncio.run(perform_rapiddns_lookup(RapidDnsSubdomainsRequest(domain="example.com")))

    assert exc_info.value.status_code == 502


def test_rapiddns_request_rejects_wildcard_patterns():
    with pytest.raises(ValueError):
        RapidDnsSubdomainsRequest(domain="example-*")


def test_rapiddns_request_normalizes_protocol_and_case():
    req = RapidDnsSubdomainsRequest(domain="HTTPS://Example.COM/path")

    assert req.domain == "example.com"
