"""
Lightweight DNSSEC signal: checks whether a domain publishes DNSKEY/DS
records via a public resolver, using the same dnspython dependency
`dns_lookup_service.py` already relies on. Presence of either record kind is
treated as "DNSSEC is set up" - a quick proxy signal for an analyst, not full
chain-of-trust validation (that needs walking the delegation chain from the
root and cross-checking each hop's DS against its parent's DNSKEY, which is
out of scope for a quick domain-recon panel).
"""

import asyncio
import logging

import dns.asyncresolver
import dns.exception
import dns.resolver

from app.features.ioc_tools.domain_finder.schemas.domain_schemas import (
    DnssecRequest,
    DnssecResponse,
)

logger = logging.getLogger(__name__)

DNS_TIMEOUT = 5.0
# Used only when the host has no usable system resolver config (e.g. macOS,
# whose /etc/resolv.conf is a stub notice file dnspython can't parse) - same
# fallback dns_lookup_service.py uses.
FALLBACK_NAMESERVERS = ["1.1.1.1", "8.8.8.8"]


def _build_resolver() -> dns.asyncresolver.Resolver:
    """Build a resolver, falling back to public resolvers if the system config is unusable"""
    try:
        resolver = dns.asyncresolver.Resolver()
    except dns.resolver.NoResolverConfiguration:
        logger.warning(
            "No usable system resolver configuration found, falling back to public resolvers"
        )
        resolver = dns.asyncresolver.Resolver(configure=False)
        resolver.nameservers = FALLBACK_NAMESERVERS

    resolver.timeout = DNS_TIMEOUT
    resolver.lifetime = DNS_TIMEOUT
    return resolver


async def perform_dnssec_lookup(request: DnssecRequest) -> DnssecResponse:
    """
    Check whether a domain publishes DNSKEY/DS records.

    Args:
        request: Validated DNSSEC request

    Returns:
        DnssecResponse with the enabled flag and the raw records found
    """
    domain = request.domain
    logger.info("Starting DNSSEC check for: %s", domain)

    resolver = _build_resolver()
    dnskey_records, ds_records = await asyncio.gather(
        _resolve(resolver, domain, "DNSKEY"),
        _resolve(resolver, domain, "DS"),
    )

    response = DnssecResponse(
        domain=domain,
        dnssec_enabled=bool(dnskey_records or ds_records),
        dnskey_records=dnskey_records,
        ds_records=ds_records,
    )
    logger.info(
        "DNSSEC check completed for %s - enabled=%s (%s DNSKEY, %s DS)",
        domain,
        response.dnssec_enabled,
        len(dnskey_records),
        len(ds_records),
    )
    return response


async def _resolve(
    resolver: dns.asyncresolver.Resolver, domain: str, record_type: str
) -> list[str]:
    """Resolve a single record type for a domain, degrading to an empty list on any failure -
    NXDOMAIN/NoAnswer/no DNSSEC published are all the same "not enabled" outcome, not errors."""
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

    return [str(rdata) for rdata in answer]
