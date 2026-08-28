"""HTTP-level coverage for domain_routes.py: every panel exposes an identical
POST(body)/GET(path) pair that builds a *Request and delegates to one
`perform_*_lookup` service - each already has its own dedicated service-level
tests, so this only checks the route wires both request shapes into it
correctly and returns its response."""

from collections.abc import AsyncGenerator
from datetime import UTC, datetime

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from app.core.config.rate_limit_config import limiter
from app.core.dependencies import get_read_db
from app.features.ioc_tools.domain_finder.routers import domain_routes
from app.features.ioc_tools.domain_finder.schemas.domain_schemas import (
    BlocklistResponse,
    CtSubdomainsResponse,
    DnsDumpsterResponse,
    DnsLookupResponse,
    DnsRecordSet,
    DnssecResponse,
    DomainLookupResponse,
    HackerTargetSubdomainsResponse,
    RapidDnsSubdomainsResponse,
    SecurityHeadersResponse,
    SslInfoResponse,
    WaybackLookupResponse,
    WhoisLookupResponse,
)


@pytest.fixture
def client():
    async def _get_read_db() -> AsyncGenerator[None]:
        yield None

    app = FastAPI()
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
    app.include_router(domain_routes.router)
    app.dependency_overrides[get_read_db] = _get_read_db
    return TestClient(app)


def _fake_service(captured, result, *, extra_arg=False):
    """Builds a stand-in for a `perform_*_lookup` service: records the
    *Request it was called with and returns `result`. `extra_arg` accounts
    for the DNSDumpster endpoints, whose service also takes `db`."""

    async def _svc(request, *rest):
        captured.append(request)
        if extra_arg:
            assert len(rest) == 1
        return result

    return _svc


class TestLookupDomain:
    def test_post_and_get_both_delegate_to_the_service(self, client, monkeypatch):
        captured = []
        result = DomainLookupResponse(domain="example.com", results=[], total_results=0)
        monkeypatch.setattr(domain_routes, "perform_domain_lookup", _fake_service(captured, result))

        post_response = client.post("/api/domain/lookup", json={"domain": "example.com"})
        get_response = client.get("/api/domain/lookup/example.com")

        assert post_response.status_code == 200
        assert get_response.status_code == 200
        assert [r.domain for r in captured] == ["example.com", "example.com"]

    def test_rejects_an_empty_domain(self, client):
        response = client.post("/api/domain/lookup", json={"domain": ""})
        assert response.status_code == 422


class TestWhoisLookup:
    def test_post_and_get_both_delegate_to_the_service(self, client, monkeypatch):
        captured = []
        result = WhoisLookupResponse(domain="example.com", rdap_server="rdap.example")
        monkeypatch.setattr(domain_routes, "perform_whois_lookup", _fake_service(captured, result))

        post_response = client.post("/api/domain/whois", json={"domain": "example.com"})
        get_response = client.get("/api/domain/whois/example.com")

        assert post_response.status_code == 200
        assert post_response.json()["rdap_server"] == "rdap.example"
        assert get_response.status_code == 200
        assert len(captured) == 2


class TestCtSubdomainsLookup:
    def test_post_and_get_both_delegate_to_the_service(self, client, monkeypatch):
        captured = []
        result = CtSubdomainsResponse(domain="example.com", total_certificates=0)
        monkeypatch.setattr(
            domain_routes, "perform_ct_subdomains_lookup", _fake_service(captured, result)
        )

        post_response = client.post("/api/domain/ct-subdomains", json={"domain": "example.com"})
        get_response = client.get("/api/domain/ct-subdomains/example.com")

        assert post_response.status_code == 200
        assert get_response.status_code == 200
        assert len(captured) == 2


class TestHackertargetSubdomainsLookup:
    def test_post_and_get_both_delegate_to_the_service(self, client, monkeypatch):
        captured = []
        result = HackerTargetSubdomainsResponse(domain="example.com", total_hosts=0)
        monkeypatch.setattr(
            domain_routes, "perform_hackertarget_lookup", _fake_service(captured, result)
        )

        post_response = client.post(
            "/api/domain/hackertarget-subdomains", json={"domain": "example.com"}
        )
        get_response = client.get("/api/domain/hackertarget-subdomains/example.com")

        assert post_response.status_code == 200
        assert get_response.status_code == 200
        assert len(captured) == 2


class TestRapiddnsSubdomainsLookup:
    def test_post_and_get_both_delegate_to_the_service(self, client, monkeypatch):
        captured = []
        result = RapidDnsSubdomainsResponse(domain="example.com", total_records=0)
        monkeypatch.setattr(
            domain_routes, "perform_rapiddns_lookup", _fake_service(captured, result)
        )

        post_response = client.post(
            "/api/domain/rapiddns-subdomains", json={"domain": "example.com"}
        )
        get_response = client.get("/api/domain/rapiddns-subdomains/example.com")

        assert post_response.status_code == 200
        assert get_response.status_code == 200
        assert len(captured) == 2


class TestSslInfoLookup:
    def test_post_and_get_both_delegate_to_the_service(self, client, monkeypatch):
        captured = []
        result = SslInfoResponse(
            domain="example.com",
            subject="CN=example.com",
            issuer="CN=Example CA",
            serial_number="01",
            not_before=datetime(2024, 1, 1, tzinfo=UTC),
            not_after=datetime(2025, 1, 1, tzinfo=UTC),
            days_until_expiry=100,
            is_expired=False,
            hostname_matches=True,
        )
        monkeypatch.setattr(
            domain_routes, "perform_ssl_info_lookup", _fake_service(captured, result)
        )

        post_response = client.post("/api/domain/ssl-info", json={"domain": "example.com"})
        get_response = client.get("/api/domain/ssl-info/example.com")

        assert post_response.status_code == 200
        assert post_response.json()["hostname_matches"] is True
        assert get_response.status_code == 200
        assert len(captured) == 2


class TestSecurityHeadersLookup:
    def test_post_and_get_both_delegate_to_the_service(self, client, monkeypatch):
        captured = []
        result = SecurityHeadersResponse(domain="example.com", status_code=200)
        monkeypatch.setattr(
            domain_routes, "perform_security_headers_lookup", _fake_service(captured, result)
        )

        post_response = client.post("/api/domain/security-headers", json={"domain": "example.com"})
        get_response = client.get("/api/domain/security-headers/example.com")

        assert post_response.status_code == 200
        assert get_response.status_code == 200
        assert len(captured) == 2


class TestDnssecLookup:
    def test_post_and_get_both_delegate_to_the_service(self, client, monkeypatch):
        captured = []
        result = DnssecResponse(domain="example.com", dnssec_enabled=True)
        monkeypatch.setattr(domain_routes, "perform_dnssec_lookup", _fake_service(captured, result))

        post_response = client.post("/api/domain/dnssec", json={"domain": "example.com"})
        get_response = client.get("/api/domain/dnssec/example.com")

        assert post_response.status_code == 200
        assert post_response.json()["dnssec_enabled"] is True
        assert get_response.status_code == 200
        assert len(captured) == 2


class TestBlocklistCheck:
    def test_post_and_get_both_delegate_to_the_service(self, client, monkeypatch):
        captured = []
        result = BlocklistResponse(domain="example.com", flagged_count=0)
        monkeypatch.setattr(
            domain_routes, "perform_blocklist_check", _fake_service(captured, result)
        )

        post_response = client.post("/api/domain/blocklist", json={"domain": "example.com"})
        get_response = client.get("/api/domain/blocklist/example.com")

        assert post_response.status_code == 200
        assert get_response.status_code == 200
        assert len(captured) == 2


class TestDnsLookup:
    def test_post_and_get_both_delegate_to_the_service(self, client, monkeypatch):
        captured = []
        result = DnsLookupResponse(domain="example.com", records=DnsRecordSet())
        monkeypatch.setattr(domain_routes, "perform_dns_lookup", _fake_service(captured, result))

        post_response = client.post("/api/domain/dns", json={"domain": "example.com"})
        get_response = client.get("/api/domain/dns/example.com")

        assert post_response.status_code == 200
        assert get_response.status_code == 200
        assert len(captured) == 2


class TestDnsdumpsterLookup:
    def test_post_and_get_both_delegate_to_the_service(self, client, monkeypatch):
        captured = []
        result = DnsDumpsterResponse(domain="example.com")
        monkeypatch.setattr(
            domain_routes,
            "perform_dnsdumpster_lookup",
            _fake_service(captured, result, extra_arg=True),
        )

        post_response = client.post("/api/domain/dnsdumpster", json={"domain": "example.com"})
        get_response = client.get("/api/domain/dnsdumpster/example.com")

        assert post_response.status_code == 200
        assert get_response.status_code == 200
        assert len(captured) == 2


class TestWaybackLookup:
    def test_post_and_get_both_delegate_to_the_service(self, client, monkeypatch):
        captured = []
        result = WaybackLookupResponse(domain="example.com", total_snapshots=0)
        monkeypatch.setattr(
            domain_routes, "perform_wayback_lookup", _fake_service(captured, result)
        )

        post_response = client.post("/api/domain/wayback", json={"domain": "example.com"})
        get_response = client.get("/api/domain/wayback/example.com")

        assert post_response.status_code == 200
        assert get_response.status_code == 200
        assert len(captured) == 2

    def test_get_passes_through_the_optional_path_query_param(self, client, monkeypatch):
        captured = []
        result = WaybackLookupResponse(domain="example.com", total_snapshots=0)
        monkeypatch.setattr(
            domain_routes, "perform_wayback_lookup", _fake_service(captured, result)
        )

        client.get("/api/domain/wayback/example.com", params={"path": "/login"})

        assert captured[0].path == "/login"


class TestHealthCheck:
    def test_reports_every_panels_endpoints(self, client):
        response = client.get("/api/domain/health")

        assert response.status_code == 200
        body = response.json()
        assert body["service"] == "domain_lookup"
        assert body["status"] == "healthy"
        assert "/api/domain/whois" in body["endpoints"]
