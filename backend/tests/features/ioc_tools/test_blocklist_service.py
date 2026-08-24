import asyncio

import dns.asyncresolver
import dns.exception
import dns.rdata
import dns.rdataclass
import dns.rdatatype
import dns.resolver
import pytest

from app.features.ioc_tools.domain_finder.schemas.domain_schemas import BlocklistRequest
from app.features.ioc_tools.domain_finder.service.blocklist_service import perform_blocklist_check

REAL_IP = "104.18.5.35"
SINKHOLE_IP = "0.0.0.0"


def _a_record(ip: str):
    return dns.rdata.from_text(dns.rdataclass.IN, dns.rdatatype.A, ip)


def test_flags_a_provider_whose_filtered_resolver_sinkholes_the_domain(monkeypatch):
    # Cloudflare's malware-blocking IPs (1.1.1.2/1.1.1.3) sinkhole; everything else
    # (including Cloudflare's own plain 1.1.1.1) returns the real address
    async def fake_resolve(self, qname, rdtype=dns.rdatatype.A, *args, **kwargs):
        if self.nameservers == ["1.1.1.2"] or self.nameservers == ["1.1.1.3"]:
            return [_a_record(SINKHOLE_IP)]
        return [_a_record(REAL_IP)]

    monkeypatch.setattr(dns.asyncresolver.Resolver, "resolve", fake_resolve)

    result = asyncio.run(perform_blocklist_check(BlocklistRequest(domain="malware.example")))

    by_provider = {r.provider: r for r in result.results}
    assert by_provider["Cloudflare (malware)"].blocked is True
    assert by_provider["Cloudflare (malware)"].filtered_answer == [SINKHOLE_IP]
    assert by_provider["Cloudflare (malware + adult)"].blocked is True
    assert by_provider["Quad9 (security)"].blocked is False
    assert by_provider["OpenDNS FamilyShield"].blocked is False
    assert result.flagged_count == 2


def test_no_providers_flag_a_clean_domain(monkeypatch):
    async def fake_resolve(self, qname, rdtype=dns.rdatatype.A, *args, **kwargs):
        return [_a_record(REAL_IP)]

    monkeypatch.setattr(dns.asyncresolver.Resolver, "resolve", fake_resolve)

    result = asyncio.run(perform_blocklist_check(BlocklistRequest(domain="example.com")))

    assert result.flagged_count == 0
    assert all(not r.blocked for r in result.results)


def test_does_not_flag_when_baseline_itself_has_no_answer(monkeypatch):
    """A domain that genuinely doesn't resolve anywhere shouldn't be reported as
    'blocked' - there's no baseline to compare against."""

    async def fake_resolve(self, qname, rdtype=dns.rdatatype.A, *args, **kwargs):
        raise dns.resolver.NXDOMAIN()

    monkeypatch.setattr(dns.asyncresolver.Resolver, "resolve", fake_resolve)

    result = asyncio.run(perform_blocklist_check(BlocklistRequest(domain="doesnotexist.example")))

    assert result.flagged_count == 0
    assert all(r.baseline_answer == [] for r in result.results)


def test_resolve_a_degrades_to_empty_list_on_timeout(monkeypatch):
    async def fake_resolve(self, qname, rdtype=dns.rdatatype.A, *args, **kwargs):
        raise dns.exception.Timeout()

    monkeypatch.setattr(dns.asyncresolver.Resolver, "resolve", fake_resolve)

    result = asyncio.run(perform_blocklist_check(BlocklistRequest(domain="example.com")))

    assert result.flagged_count == 0


def test_blocklist_request_rejects_wildcard_patterns():
    with pytest.raises(ValueError):
        BlocklistRequest(domain="example-*")


def test_blocklist_request_normalizes_protocol_and_case():
    req = BlocklistRequest(domain="HTTPS://Example.COM/path")

    assert req.domain == "example.com"
