import asyncio

import pytest

from app.core.exceptions import AppHTTPException
from app.features.ioc_tools.domain_finder.schemas.domain_schemas import (
    HackerTargetSubdomainsRequest,
)
from app.features.ioc_tools.domain_finder.service import hackertarget_lookup_service
from app.features.ioc_tools.domain_finder.service.hackertarget_lookup_service import (
    perform_hackertarget_lookup,
)


def test_perform_hackertarget_lookup_dedupes_and_sorts_subdomains(monkeypatch):
    async def fake_fetch(domain):
        return [
            ("www.example.com", "1.1.1.1"),
            ("api.example.com", "2.2.2.2"),
            ("www.example.com", "1.1.1.1"),
        ]

    monkeypatch.setattr(hackertarget_lookup_service, "fetch_hackertarget_hosts", fake_fetch)

    result = asyncio.run(
        perform_hackertarget_lookup(HackerTargetSubdomainsRequest(domain="example.com"))
    )

    assert result.domain == "example.com"
    assert result.subdomains == ["api.example.com", "www.example.com"]
    assert result.total_hosts == 3


def test_perform_hackertarget_lookup_excludes_unrelated_hosts_from_subdomains(monkeypatch):
    async def fake_fetch(domain):
        return [("www.example.com", "1.1.1.1"), ("unrelated-host.net", "3.3.3.3")]

    monkeypatch.setattr(hackertarget_lookup_service, "fetch_hackertarget_hosts", fake_fetch)

    result = asyncio.run(
        perform_hackertarget_lookup(HackerTargetSubdomainsRequest(domain="example.com"))
    )

    assert result.subdomains == ["www.example.com"]
    # Still surfaced in the raw host list, just not counted as a subdomain
    assert len(result.hosts) == 2


def test_perform_hackertarget_lookup_handles_empty_response(monkeypatch):
    async def fake_fetch(domain):
        return []

    monkeypatch.setattr(hackertarget_lookup_service, "fetch_hackertarget_hosts", fake_fetch)

    result = asyncio.run(
        perform_hackertarget_lookup(HackerTargetSubdomainsRequest(domain="doesnotexist.example"))
    )

    assert result.subdomains == []
    assert result.total_hosts == 0


def test_perform_hackertarget_lookup_propagates_fetch_errors(monkeypatch):
    async def fake_fetch(domain):
        raise AppHTTPException(
            status_code=429, detail="quota exceeded", error_code="HACKERTARGET_RATE_LIMITED"
        )

    monkeypatch.setattr(hackertarget_lookup_service, "fetch_hackertarget_hosts", fake_fetch)

    with pytest.raises(AppHTTPException) as exc_info:
        asyncio.run(
            perform_hackertarget_lookup(HackerTargetSubdomainsRequest(domain="example.com"))
        )

    assert exc_info.value.status_code == 429


def test_hackertarget_request_rejects_wildcard_patterns():
    with pytest.raises(ValueError):
        HackerTargetSubdomainsRequest(domain="example-*")


def test_hackertarget_request_normalizes_protocol_and_case():
    req = HackerTargetSubdomainsRequest(domain="HTTPS://Example.COM/path")

    assert req.domain == "example.com"
