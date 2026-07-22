"""
DNS record lookup business logic: resolves the common record types directly
against public resolvers via dnspython (no paid passive-DNS provider needed),
plus reverse DNS (PTR) for any IPs found in the A/AAAA answers.

A missing record type (NXDOMAIN, NoAnswer, no responding nameserver, timeout)
is a normal outcome for a DNS lookup, not a failure of the request, so each
record type degrades to an empty list independently instead of failing the
whole lookup.
"""
import asyncio
import logging
from typing import Any

import dns.asyncresolver
import dns.exception
import dns.rdatatype
import dns.resolver
import dns.reversename

from app.features.ioc_tools.domain_finder.schemas.domain_schemas import (
    DnsLookupRequest,
    DnsLookupResponse,
    DnsRecordSet,
)

logger = logging.getLogger(__name__)

RECORD_TYPES = ["A", "AAAA", "MX", "TXT", "NS", "CNAME"]
DNS_TIMEOUT = 5.0
# Used only when the host has no usable system resolver config (e.g. macOS,
# whose /etc/resolv.conf is a stub notice file dnspython can't parse).
FALLBACK_NAMESERVERS = ["1.1.1.1", "8.8.8.8"]


def _build_resolver() -> dns.asyncresolver.Resolver:
    """Build a resolver, falling back to public resolvers if the system config is unusable"""
    try:
        resolver = dns.asyncresolver.Resolver()
    except dns.resolver.NoResolverConfiguration:
        logger.warning("No usable system resolver configuration found, falling back to public resolvers")
        resolver = dns.asyncresolver.Resolver(configure=False)
        resolver.nameservers = FALLBACK_NAMESERVERS

    resolver.timeout = DNS_TIMEOUT
    resolver.lifetime = DNS_TIMEOUT
    return resolver


async def perform_dns_lookup(dns_request: DnsLookupRequest) -> DnsLookupResponse:
    """
    Resolve A/AAAA/MX/TXT/NS/CNAME records for a domain, plus reverse DNS for
    any IPs found.

    Args:
        dns_request: Validated DNS lookup request containing the domain to resolve

    Returns:
        DnsLookupResponse containing the resolved records and reverse DNS results
    """
    domain = dns_request.domain
    logger.info("Starting DNS lookup for: %s", domain)

    resolver = _build_resolver()

    resolved = await asyncio.gather(
        *(_resolve_record_type(resolver, domain, record_type) for record_type in RECORD_TYPES)
    )
    records = DnsRecordSet(**dict(zip(RECORD_TYPES, resolved)))

    ip_addresses = sorted(set(records.A) | set(records.AAAA))
    reverse_results = await asyncio.gather(
        *(_reverse_lookup(resolver, ip) for ip in ip_addresses)
    )
    reverse_dns = {ip: hosts for ip, hosts in zip(ip_addresses, reverse_results) if hosts}

    response = DnsLookupResponse(domain=domain, records=records, reverse_dns=reverse_dns)
    logger.info(
        "DNS lookup completed for %s - record counts: %s",
        domain, {rtype: len(getattr(records, rtype)) for rtype in RECORD_TYPES},
    )
    return response


async def _resolve_record_type(resolver: dns.asyncresolver.Resolver, domain: str, record_type: str) -> list[str]:
    """Resolve a single DNS record type for a domain, degrading to an empty list on any failure"""
    try:
        answer = await resolver.resolve(domain, record_type)
    except dns.resolver.NXDOMAIN:
        logger.info("NXDOMAIN resolving %s records for %s", record_type, domain)
        return []
    except dns.resolver.NoAnswer:
        logger.debug("No %s records for %s", record_type, domain)
        return []
    except dns.resolver.NoNameservers as e:
        logger.warning("No nameservers responded for %s %s: %s", domain, record_type, e)
        return []
    except dns.exception.Timeout:
        logger.warning("Timeout resolving %s records for %s", record_type, domain)
        return []
    except Exception as e:
        logger.warning("Unexpected error resolving %s records for %s: %s", record_type, domain, e)
        return []

    return [_format_rdata(record_type, rdata) for rdata in answer]


async def _reverse_lookup(resolver: dns.asyncresolver.Resolver, ip: str) -> list[str]:
    """Resolve the PTR hostname(s) for a single IP address, degrading to an empty list on any failure"""
    try:
        reverse_name = dns.reversename.from_address(ip)
        answer = await resolver.resolve(reverse_name, "PTR")
        return [str(rdata.target).rstrip(".") for rdata in answer]
    except Exception as e:
        logger.debug("Reverse DNS lookup failed for %s: %s", ip, e)
        return []


def _format_rdata(record_type: str, rdata: Any) -> str:
    """Format a single dnspython rdata object into a plain, UI-friendly string"""
    if record_type == "MX":
        return f"{rdata.preference} {str(rdata.exchange).rstrip('.')}"
    if record_type == "TXT":
        return b"".join(rdata.strings).decode("utf-8", errors="replace")
    return str(rdata).rstrip(".")
