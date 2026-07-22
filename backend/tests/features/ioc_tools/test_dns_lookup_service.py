import asyncio

import dns.asyncresolver
import dns.rdata
import dns.rdataclass
import dns.rdatatype
import dns.resolver
import pytest

from app.features.ioc_tools.domain_finder.schemas.domain_schemas import DnsLookupRequest
from app.features.ioc_tools.domain_finder.service.dns_lookup_service import (
    _format_rdata,
    perform_dns_lookup,
)


def _rdata(rdtype_name, text):
    return dns.rdata.from_text(dns.rdataclass.IN, getattr(dns.rdatatype, rdtype_name), text)


def test_format_rdata_a_returns_plain_ip():
    assert _format_rdata("A", _rdata("A", "93.184.216.34")) == "93.184.216.34"


def test_format_rdata_mx_includes_preference_and_strips_dot():
    assert _format_rdata("MX", _rdata("MX", "10 mail.example.com.")) == "10 mail.example.com"


def test_format_rdata_txt_decodes_strings():
    assert _format_rdata("TXT", _rdata("TXT", '"v=spf1 -all"')) == "v=spf1 -all"


def test_format_rdata_ns_strips_trailing_dot():
    assert _format_rdata("NS", _rdata("NS", "ns1.example.com.")) == "ns1.example.com"


def test_dns_request_rejects_wildcard_patterns():
    with pytest.raises(ValueError):
        DnsLookupRequest(domain="example-*")


def test_dns_request_normalizes_protocol_and_path():
    req = DnsLookupRequest(domain="HTTPS://Example.COM/path")
    assert req.domain == "example.com"


def test_perform_dns_lookup_resolves_records_and_reverse_dns(monkeypatch):
    async def fake_resolve(self, qname, rdtype=dns.rdatatype.A, *args, **kwargs):
        if rdtype == "A":
            return [_rdata("A", "93.184.216.34")]
        if rdtype == "AAAA":
            raise dns.resolver.NoAnswer()
        if rdtype == "MX":
            return [_rdata("MX", "10 mail.example.com.")]
        if rdtype == "TXT":
            return [_rdata("TXT", '"v=spf1 -all"')]
        if rdtype == "NS":
            return [_rdata("NS", "ns1.example.com.")]
        if rdtype == "CNAME":
            raise dns.resolver.NoAnswer()
        if rdtype == "PTR":
            return [_rdata("PTR", "host.example.com.")]
        raise AssertionError(f"unexpected rdtype {rdtype}")

    monkeypatch.setattr(dns.asyncresolver.Resolver, "resolve", fake_resolve)

    result = asyncio.run(perform_dns_lookup(DnsLookupRequest(domain="example.com")))

    assert result.domain == "example.com"
    assert result.records.A == ["93.184.216.34"]
    assert result.records.AAAA == []
    assert result.records.MX == ["10 mail.example.com"]
    assert result.records.TXT == ["v=spf1 -all"]
    assert result.records.NS == ["ns1.example.com"]
    assert result.records.CNAME == []
    assert result.reverse_dns == {"93.184.216.34": ["host.example.com"]}


def test_perform_dns_lookup_handles_nxdomain_for_all_types(monkeypatch):
    async def fake_resolve(self, qname, rdtype=dns.rdatatype.A, *args, **kwargs):
        raise dns.resolver.NXDOMAIN()

    monkeypatch.setattr(dns.asyncresolver.Resolver, "resolve", fake_resolve)

    result = asyncio.run(perform_dns_lookup(DnsLookupRequest(domain="doesnotexist.example")))

    assert result.records.model_dump() == {"A": [], "AAAA": [], "MX": [], "TXT": [], "NS": [], "CNAME": []}
    assert result.reverse_dns == {}


def test_perform_dns_lookup_skips_reverse_lookup_when_no_ips_found(monkeypatch):
    async def fake_resolve(self, qname, rdtype=dns.rdatatype.A, *args, **kwargs):
        if rdtype == "PTR":
            raise AssertionError("PTR lookup should not run when no A/AAAA records were found")
        raise dns.resolver.NoAnswer()

    monkeypatch.setattr(dns.asyncresolver.Resolver, "resolve", fake_resolve)

    result = asyncio.run(perform_dns_lookup(DnsLookupRequest(domain="example.com")))

    assert result.reverse_dns == {}


def test_perform_dns_lookup_ignores_reverse_lookup_failures(monkeypatch):
    async def fake_resolve(self, qname, rdtype=dns.rdatatype.A, *args, **kwargs):
        if rdtype == "A":
            return [_rdata("A", "93.184.216.34")]
        if rdtype == "PTR":
            raise dns.resolver.NXDOMAIN()
        raise dns.resolver.NoAnswer()

    monkeypatch.setattr(dns.asyncresolver.Resolver, "resolve", fake_resolve)

    result = asyncio.run(perform_dns_lookup(DnsLookupRequest(domain="example.com")))

    assert result.records.A == ["93.184.216.34"]
    assert result.reverse_dns == {}
