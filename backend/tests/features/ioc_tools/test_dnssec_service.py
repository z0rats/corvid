import asyncio

import dns.asyncresolver
import dns.exception
import dns.rdata
import dns.rdataclass
import dns.rdatatype
import dns.resolver
import pytest

from app.features.ioc_tools.domain_finder.schemas.domain_schemas import DnssecRequest
from app.features.ioc_tools.domain_finder.service.dnssec_service import perform_dnssec_lookup


def _rdata(rdtype_name, text):
    return dns.rdata.from_text(dns.rdataclass.IN, getattr(dns.rdatatype, rdtype_name), text)


def test_perform_dnssec_lookup_enabled_when_dnskey_present(monkeypatch):
    async def fake_resolve(self, qname, rdtype=dns.rdatatype.A, *args, **kwargs):
        if rdtype == "DNSKEY":
            return [_rdata("DNSKEY", "256 3 13 AQID")]
        if rdtype == "DS":
            raise dns.resolver.NoAnswer()
        raise AssertionError(f"unexpected rdtype {rdtype}")

    monkeypatch.setattr(dns.asyncresolver.Resolver, "resolve", fake_resolve)

    result = asyncio.run(perform_dnssec_lookup(DnssecRequest(domain="example.com")))

    assert result.domain == "example.com"
    assert result.dnssec_enabled is True
    assert len(result.dnskey_records) == 1
    assert result.ds_records == []


def test_perform_dnssec_lookup_enabled_when_only_ds_present(monkeypatch):
    async def fake_resolve(self, qname, rdtype=dns.rdatatype.A, *args, **kwargs):
        if rdtype == "DNSKEY":
            raise dns.resolver.NoAnswer()
        if rdtype == "DS":
            return [
                _rdata(
                    "DS",
                    "2371 13 2 32996839A6D808AFE3EB4A795A0E6A7A39A76FC52FF228B22B76F6D63826F2B9",
                )
            ]
        raise AssertionError(f"unexpected rdtype {rdtype}")

    monkeypatch.setattr(dns.asyncresolver.Resolver, "resolve", fake_resolve)

    result = asyncio.run(perform_dnssec_lookup(DnssecRequest(domain="example.com")))

    assert result.dnssec_enabled is True
    assert result.dnskey_records == []
    assert len(result.ds_records) == 1


def test_perform_dnssec_lookup_disabled_when_neither_present(monkeypatch):
    async def fake_resolve(self, qname, rdtype=dns.rdatatype.A, *args, **kwargs):
        raise dns.resolver.NoAnswer()

    monkeypatch.setattr(dns.asyncresolver.Resolver, "resolve", fake_resolve)

    result = asyncio.run(perform_dnssec_lookup(DnssecRequest(domain="example.com")))

    assert result.dnssec_enabled is False
    assert result.dnskey_records == []
    assert result.ds_records == []


def test_perform_dnssec_lookup_handles_nxdomain(monkeypatch):
    async def fake_resolve(self, qname, rdtype=dns.rdatatype.A, *args, **kwargs):
        raise dns.resolver.NXDOMAIN()

    monkeypatch.setattr(dns.asyncresolver.Resolver, "resolve", fake_resolve)

    result = asyncio.run(perform_dnssec_lookup(DnssecRequest(domain="doesnotexist.example")))

    assert result.dnssec_enabled is False


def test_perform_dnssec_lookup_handles_timeout(monkeypatch):
    async def fake_resolve(self, qname, rdtype=dns.rdatatype.A, *args, **kwargs):
        raise dns.exception.Timeout()

    monkeypatch.setattr(dns.asyncresolver.Resolver, "resolve", fake_resolve)

    result = asyncio.run(perform_dnssec_lookup(DnssecRequest(domain="example.com")))

    assert result.dnssec_enabled is False


def test_dnssec_request_rejects_wildcard_patterns():
    with pytest.raises(ValueError):
        DnssecRequest(domain="example-*")


def test_dnssec_request_normalizes_protocol_and_case():
    req = DnssecRequest(domain="HTTPS://Example.COM/path")

    assert req.domain == "example.com"
