"""Domain lookup API routes"""

import logging
from typing import Any

from fastapi import APIRouter, Request, status

from app.core.config.rate_limit_config import limiter
from app.core.dependencies import ReadSessionDep
from app.features.ioc_tools.domain_finder.schemas.domain_schemas import (
    BlocklistRequest,
    BlocklistResponse,
    CtSubdomainsRequest,
    CtSubdomainsResponse,
    DnsDumpsterRequest,
    DnsDumpsterResponse,
    DnsLookupRequest,
    DnsLookupResponse,
    DnssecRequest,
    DnssecResponse,
    DomainLookupRequest,
    DomainLookupResponse,
    HackerTargetSubdomainsRequest,
    HackerTargetSubdomainsResponse,
    RapidDnsSubdomainsRequest,
    RapidDnsSubdomainsResponse,
    SecurityHeadersRequest,
    SecurityHeadersResponse,
    SslInfoRequest,
    SslInfoResponse,
    WaybackLookupRequest,
    WaybackLookupResponse,
    WhoisLookupRequest,
    WhoisLookupResponse,
)
from app.features.ioc_tools.domain_finder.service.blocklist_service import perform_blocklist_check
from app.features.ioc_tools.domain_finder.service.ct_subdomains_service import (
    perform_ct_subdomains_lookup,
)
from app.features.ioc_tools.domain_finder.service.dns_lookup_service import perform_dns_lookup
from app.features.ioc_tools.domain_finder.service.dnsdumpster_service import (
    perform_dnsdumpster_lookup,
)
from app.features.ioc_tools.domain_finder.service.dnssec_service import perform_dnssec_lookup
from app.features.ioc_tools.domain_finder.service.domain_lookup_service import perform_domain_lookup
from app.features.ioc_tools.domain_finder.service.hackertarget_lookup_service import (
    perform_hackertarget_lookup,
)
from app.features.ioc_tools.domain_finder.service.rapiddns_lookup_service import (
    perform_rapiddns_lookup,
)
from app.features.ioc_tools.domain_finder.service.security_headers_service import (
    perform_security_headers_lookup,
)
from app.features.ioc_tools.domain_finder.service.ssl_info_service import perform_ssl_info_lookup
from app.features.ioc_tools.domain_finder.service.wayback_lookup_service import (
    perform_wayback_lookup,
)
from app.features.ioc_tools.domain_finder.service.whois_lookup_service import perform_whois_lookup

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/domain", tags=["Domain Lookup"])


@router.post(
    "/lookup",
    response_model=DomainLookupResponse,
    status_code=status.HTTP_200_OK,
    summary="Perform domain lookup using URLScan.io",
    description=(
        "Lookup domain information using the URLScan.io API to find scan "
        "results and security information"
    ),
)
@limiter.limit("30/minute")
async def lookup_domain_post(
    request: Request, domain_request: DomainLookupRequest
) -> DomainLookupResponse:
    """Perform comprehensive domain lookup using URLScan.io API via POST request"""
    logger.info("POST domain lookup request - Domain: %s", domain_request.domain)
    result = await perform_domain_lookup(domain_request)
    logger.info(
        "POST domain lookup completed - Domain: %s, Results: %s",
        domain_request.domain,
        result.total_results,
    )
    return result


@router.get(
    "/lookup/{domain}",
    response_model=DomainLookupResponse,
    status_code=status.HTTP_200_OK,
    summary="Perform domain lookup via URL parameter",
    description="Lookup domain information using URL parameter for simple GET requests",
)
@limiter.limit("30/minute")
async def lookup_domain_get(request: Request, domain: str) -> DomainLookupResponse:
    """Perform domain lookup using domain from URL path via GET request"""
    logger.info("GET domain lookup request - Domain: %s", domain)
    domain_request = DomainLookupRequest(domain=domain)
    result = await perform_domain_lookup(domain_request)
    logger.info(
        "GET domain lookup completed - Domain: %s, Results: %s", domain, result.total_results
    )
    return result


@router.post(
    "/whois",
    response_model=WhoisLookupResponse,
    status_code=status.HTTP_200_OK,
    summary="Perform WHOIS lookup via RDAP",
    description=(
        "Look up domain registration data (registrar, creation/expiry/updated "
        "dates, registrant org, nameservers) via RDAP"
    ),
)
@limiter.limit("30/minute")
async def whois_lookup_post(
    request: Request, whois_request: WhoisLookupRequest
) -> WhoisLookupResponse:
    """Perform WHOIS/RDAP lookup for a domain via POST request"""
    logger.info("POST WHOIS lookup request - Domain: %s", whois_request.domain)
    result = await perform_whois_lookup(whois_request)
    logger.info("POST WHOIS lookup completed - Domain: %s", whois_request.domain)
    return result


@router.get(
    "/whois/{domain}",
    response_model=WhoisLookupResponse,
    status_code=status.HTTP_200_OK,
    summary="Perform WHOIS lookup via URL parameter",
    description="Look up domain registration data via RDAP using domain from URL path",
)
@limiter.limit("30/minute")
async def whois_lookup_get(request: Request, domain: str) -> WhoisLookupResponse:
    """Perform WHOIS/RDAP lookup for a domain via GET request"""
    logger.info("GET WHOIS lookup request - Domain: %s", domain)
    whois_request = WhoisLookupRequest(domain=domain)
    result = await perform_whois_lookup(whois_request)
    logger.info("GET WHOIS lookup completed - Domain: %s", domain)
    return result


@router.post(
    "/ct-subdomains",
    response_model=CtSubdomainsResponse,
    status_code=status.HTTP_200_OK,
    summary="Enumerate subdomains via Certificate Transparency logs",
    description=(
        "Query crt.sh's Certificate Transparency log mirror to enumerate "
        "subdomains and cert issuance history for a domain"
    ),
)
@limiter.limit("30/minute")
async def ct_subdomains_lookup_post(
    request: Request, ct_request: CtSubdomainsRequest
) -> CtSubdomainsResponse:
    """Perform a Certificate Transparency subdomain lookup via POST request"""
    logger.info("POST CT subdomains lookup request - Domain: %s", ct_request.domain)
    result = await perform_ct_subdomains_lookup(ct_request)
    logger.info(
        "POST CT subdomains lookup completed - Domain: %s, Subdomains: %s",
        ct_request.domain,
        len(result.subdomains),
    )
    return result


@router.get(
    "/ct-subdomains/{domain}",
    response_model=CtSubdomainsResponse,
    status_code=status.HTTP_200_OK,
    summary="Enumerate subdomains via Certificate Transparency logs via URL parameter",
    description="Query crt.sh using domain from URL path for simple GET requests",
)
@limiter.limit("30/minute")
async def ct_subdomains_lookup_get(request: Request, domain: str) -> CtSubdomainsResponse:
    """Perform a Certificate Transparency subdomain lookup using domain from URL path via GET
    request"""
    logger.info("GET CT subdomains lookup request - Domain: %s", domain)
    ct_request = CtSubdomainsRequest(domain=domain)
    result = await perform_ct_subdomains_lookup(ct_request)
    logger.info(
        "GET CT subdomains lookup completed - Domain: %s, Subdomains: %s",
        domain,
        len(result.subdomains),
    )
    return result


@router.post(
    "/hackertarget-subdomains",
    response_model=HackerTargetSubdomainsResponse,
    status_code=status.HTTP_200_OK,
    summary="Enumerate subdomains via HackerTarget's hostsearch API",
    description=(
        "Query HackerTarget's free hostsearch API to enumerate subdomains and their "
        "resolved IPs for a domain"
    ),
)
@limiter.limit("30/minute")
async def hackertarget_subdomains_lookup_post(
    request: Request, hackertarget_request: HackerTargetSubdomainsRequest
) -> HackerTargetSubdomainsResponse:
    """Perform a HackerTarget subdomain lookup via POST request"""
    logger.info(
        "POST HackerTarget subdomains lookup request - Domain: %s", hackertarget_request.domain
    )
    result = await perform_hackertarget_lookup(hackertarget_request)
    logger.info(
        "POST HackerTarget subdomains lookup completed - Domain: %s, Subdomains: %s",
        hackertarget_request.domain,
        len(result.subdomains),
    )
    return result


@router.get(
    "/hackertarget-subdomains/{domain}",
    response_model=HackerTargetSubdomainsResponse,
    status_code=status.HTTP_200_OK,
    summary="Enumerate subdomains via HackerTarget's hostsearch API via URL parameter",
    description="Query HackerTarget's hostsearch API using domain from URL path for simple GET "
    "requests",
)
@limiter.limit("30/minute")
async def hackertarget_subdomains_lookup_get(
    request: Request, domain: str
) -> HackerTargetSubdomainsResponse:
    """Perform a HackerTarget subdomain lookup using domain from URL path via GET request"""
    logger.info("GET HackerTarget subdomains lookup request - Domain: %s", domain)
    hackertarget_request = HackerTargetSubdomainsRequest(domain=domain)
    result = await perform_hackertarget_lookup(hackertarget_request)
    logger.info(
        "GET HackerTarget subdomains lookup completed - Domain: %s, Subdomains: %s",
        domain,
        len(result.subdomains),
    )
    return result


@router.post(
    "/rapiddns-subdomains",
    response_model=RapidDnsSubdomainsResponse,
    status_code=status.HTTP_200_OK,
    summary="Enumerate subdomains via RapidDNS",
    description=(
        "Query RapidDNS's public subdomain lookup page to enumerate subdomains and their "
        "DNS records for a domain"
    ),
)
@limiter.limit("30/minute")
async def rapiddns_subdomains_lookup_post(
    request: Request, rapiddns_request: RapidDnsSubdomainsRequest
) -> RapidDnsSubdomainsResponse:
    """Perform a RapidDNS subdomain lookup via POST request"""
    logger.info("POST RapidDNS subdomains lookup request - Domain: %s", rapiddns_request.domain)
    result = await perform_rapiddns_lookup(rapiddns_request)
    logger.info(
        "POST RapidDNS subdomains lookup completed - Domain: %s, Subdomains: %s",
        rapiddns_request.domain,
        len(result.subdomains),
    )
    return result


@router.get(
    "/rapiddns-subdomains/{domain}",
    response_model=RapidDnsSubdomainsResponse,
    status_code=status.HTTP_200_OK,
    summary="Enumerate subdomains via RapidDNS via URL parameter",
    description="Query RapidDNS's subdomain lookup page using domain from URL path for simple "
    "GET requests",
)
@limiter.limit("30/minute")
async def rapiddns_subdomains_lookup_get(
    request: Request, domain: str
) -> RapidDnsSubdomainsResponse:
    """Perform a RapidDNS subdomain lookup using domain from URL path via GET request"""
    logger.info("GET RapidDNS subdomains lookup request - Domain: %s", domain)
    rapiddns_request = RapidDnsSubdomainsRequest(domain=domain)
    result = await perform_rapiddns_lookup(rapiddns_request)
    logger.info(
        "GET RapidDNS subdomains lookup completed - Domain: %s, Subdomains: %s",
        domain,
        len(result.subdomains),
    )
    return result


@router.post(
    "/ssl-info",
    response_model=SslInfoResponse,
    status_code=status.HTTP_200_OK,
    summary="Inspect a domain's TLS certificate",
    description=(
        "Connect to a domain on port 443 and parse the TLS certificate it presents "
        "(subject, issuer, validity, SAN, hostname match) - certificate verification is "
        "deliberately skipped so self-signed/expired/mismatched certificates are still shown"
    ),
)
@limiter.limit("30/minute")
async def ssl_info_lookup_post(request: Request, ssl_request: SslInfoRequest) -> SslInfoResponse:
    """Perform a TLS certificate inspection via POST request"""
    logger.info("POST SSL info request - Domain: %s", ssl_request.domain)
    result = await perform_ssl_info_lookup(ssl_request)
    logger.info(
        "POST SSL info completed - Domain: %s, Expired: %s", ssl_request.domain, result.is_expired
    )
    return result


@router.get(
    "/ssl-info/{domain}",
    response_model=SslInfoResponse,
    status_code=status.HTTP_200_OK,
    summary="Inspect a domain's TLS certificate via URL parameter",
    description="Inspect a domain's TLS certificate using domain from URL path for simple GET "
    "requests",
)
@limiter.limit("30/minute")
async def ssl_info_lookup_get(request: Request, domain: str) -> SslInfoResponse:
    """Perform a TLS certificate inspection using domain from URL path via GET request"""
    logger.info("GET SSL info request - Domain: %s", domain)
    ssl_request = SslInfoRequest(domain=domain)
    result = await perform_ssl_info_lookup(ssl_request)
    logger.info("GET SSL info completed - Domain: %s, Expired: %s", domain, result.is_expired)
    return result


@router.post(
    "/security-headers",
    response_model=SecurityHeadersResponse,
    status_code=status.HTTP_200_OK,
    summary="Audit a domain's HTTPS security headers",
    description=(
        "Fetch a domain over HTTPS and check for baseline security response headers "
        "(HSTS, CSP, X-Frame-Options, etc.), with a dedicated HSTS directive parse"
    ),
)
@limiter.limit("30/minute")
async def security_headers_lookup_post(
    request: Request, headers_request: SecurityHeadersRequest
) -> SecurityHeadersResponse:
    """Perform a security headers audit via POST request"""
    logger.info("POST security headers request - Domain: %s", headers_request.domain)
    result = await perform_security_headers_lookup(headers_request)
    logger.info(
        "POST security headers completed - Domain: %s, Present: %s, Missing: %s",
        headers_request.domain,
        len(result.present_headers),
        len(result.missing_headers),
    )
    return result


@router.get(
    "/security-headers/{domain}",
    response_model=SecurityHeadersResponse,
    status_code=status.HTTP_200_OK,
    summary="Audit a domain's HTTPS security headers via URL parameter",
    description="Audit a domain's HTTPS security headers using domain from URL path for simple "
    "GET requests",
)
@limiter.limit("30/minute")
async def security_headers_lookup_get(request: Request, domain: str) -> SecurityHeadersResponse:
    """Perform a security headers audit using domain from URL path via GET request"""
    logger.info("GET security headers request - Domain: %s", domain)
    headers_request = SecurityHeadersRequest(domain=domain)
    result = await perform_security_headers_lookup(headers_request)
    logger.info(
        "GET security headers completed - Domain: %s, Present: %s, Missing: %s",
        domain,
        len(result.present_headers),
        len(result.missing_headers),
    )
    return result


@router.post(
    "/dnssec",
    response_model=DnssecResponse,
    status_code=status.HTTP_200_OK,
    summary="Check whether a domain publishes DNSSEC records",
    description="Check a domain for published DNSKEY/DS records as a quick DNSSEC signal",
)
@limiter.limit("30/minute")
async def dnssec_lookup_post(request: Request, dnssec_request: DnssecRequest) -> DnssecResponse:
    """Perform a DNSSEC signal check via POST request"""
    logger.info("POST DNSSEC request - Domain: %s", dnssec_request.domain)
    result = await perform_dnssec_lookup(dnssec_request)
    logger.info(
        "POST DNSSEC completed - Domain: %s, Enabled: %s",
        dnssec_request.domain,
        result.dnssec_enabled,
    )
    return result


@router.get(
    "/dnssec/{domain}",
    response_model=DnssecResponse,
    status_code=status.HTTP_200_OK,
    summary="Check whether a domain publishes DNSSEC records via URL parameter",
    description="Check a domain for published DNSKEY/DS records using domain from URL path",
)
@limiter.limit("30/minute")
async def dnssec_lookup_get(request: Request, domain: str) -> DnssecResponse:
    """Perform a DNSSEC signal check using domain from URL path via GET request"""
    logger.info("GET DNSSEC request - Domain: %s", domain)
    dnssec_request = DnssecRequest(domain=domain)
    result = await perform_dnssec_lookup(dnssec_request)
    logger.info("GET DNSSEC completed - Domain: %s, Enabled: %s", domain, result.dnssec_enabled)
    return result


@router.post(
    "/blocklist",
    response_model=BlocklistResponse,
    status_code=status.HTTP_200_OK,
    summary="Check a domain against public DNS-filtering resolvers",
    description=(
        "Query a domain via several public providers' security-filtering DNS resolver and "
        "compare against that provider's plain resolver to detect DNS-level blocking/sinkholing"
    ),
)
@limiter.limit("30/minute")
async def blocklist_check_post(
    request: Request, blocklist_request: BlocklistRequest
) -> BlocklistResponse:
    """Perform a DNS blocklist check via POST request"""
    logger.info("POST blocklist check request - Domain: %s", blocklist_request.domain)
    result = await perform_blocklist_check(blocklist_request)
    logger.info(
        "POST blocklist check completed - Domain: %s, Flagged: %s",
        blocklist_request.domain,
        result.flagged_count,
    )
    return result


@router.get(
    "/blocklist/{domain}",
    response_model=BlocklistResponse,
    status_code=status.HTTP_200_OK,
    summary="Check a domain against public DNS-filtering resolvers via URL parameter",
    description="Check a domain against public DNS-filtering resolvers using domain from URL path",
)
@limiter.limit("30/minute")
async def blocklist_check_get(request: Request, domain: str) -> BlocklistResponse:
    """Perform a DNS blocklist check using domain from URL path via GET request"""
    logger.info("GET blocklist check request - Domain: %s", domain)
    blocklist_request = BlocklistRequest(domain=domain)
    result = await perform_blocklist_check(blocklist_request)
    logger.info(
        "GET blocklist check completed - Domain: %s, Flagged: %s", domain, result.flagged_count
    )
    return result


@router.post(
    "/dns",
    response_model=DnsLookupResponse,
    status_code=status.HTTP_200_OK,
    summary="Perform DNS record lookup",
    description=(
        "Resolve A/AAAA/MX/TXT/NS/CNAME records for a domain, plus reverse DNS "
        "(PTR) for any resolved IPs"
    ),
)
@limiter.limit("30/minute")
async def dns_lookup_post(request: Request, dns_request: DnsLookupRequest) -> DnsLookupResponse:
    """Perform a DNS record lookup via POST request"""
    logger.info("POST DNS lookup request - Domain: %s", dns_request.domain)
    result = await perform_dns_lookup(dns_request)
    logger.info("POST DNS lookup completed - Domain: %s", dns_request.domain)
    return result


@router.get(
    "/dns/{domain}",
    response_model=DnsLookupResponse,
    status_code=status.HTTP_200_OK,
    summary="Perform DNS record lookup via URL parameter",
    description="Resolve DNS records for a domain from URL path via GET request",
)
@limiter.limit("30/minute")
async def dns_lookup_get(request: Request, domain: str) -> DnsLookupResponse:
    """Perform a DNS record lookup using domain from URL path via GET request"""
    logger.info("GET DNS lookup request - Domain: %s", domain)
    dns_request = DnsLookupRequest(domain=domain)
    result = await perform_dns_lookup(dns_request)
    logger.info("GET DNS lookup completed - Domain: %s", domain)
    return result


@router.post(
    "/dnsdumpster",
    response_model=DnsDumpsterResponse,
    status_code=status.HTTP_200_OK,
    summary="Perform a DNSDumpster domain lookup",
    description=(
        "Look up DNS records, ASN/geo, reverse DNS, and HTTP(S) banners for a "
        "domain via the DNSDumpster API. Requires a DNSDumpster API key "
        "configured under Settings > API Keys."
    ),
)
@limiter.limit("30/minute")
async def dnsdumpster_lookup_post(
    request: Request, dnsdumpster_request: DnsDumpsterRequest, db: ReadSessionDep
) -> DnsDumpsterResponse:
    """Perform a DNSDumpster domain lookup via POST request"""
    logger.info("POST DNSDumpster lookup request - Domain: %s", dnsdumpster_request.domain)
    result = await perform_dnsdumpster_lookup(dnsdumpster_request, db)
    logger.info("POST DNSDumpster lookup completed - Domain: %s", dnsdumpster_request.domain)
    return result


@router.get(
    "/dnsdumpster/{domain}",
    response_model=DnsDumpsterResponse,
    status_code=status.HTTP_200_OK,
    summary="Perform a DNSDumpster domain lookup via URL parameter",
    description=(
        "Look up DNS records, ASN/geo, reverse DNS, and HTTP(S) banners for a domain via URL path"
    ),
)
@limiter.limit("30/minute")
async def dnsdumpster_lookup_get(
    request: Request, domain: str, db: ReadSessionDep
) -> DnsDumpsterResponse:
    """Perform a DNSDumpster domain lookup using domain from URL path via GET request"""
    logger.info("GET DNSDumpster lookup request - Domain: %s", domain)
    dnsdumpster_request = DnsDumpsterRequest(domain=domain)
    result = await perform_dnsdumpster_lookup(dnsdumpster_request, db)
    logger.info("GET DNSDumpster lookup completed - Domain: %s", domain)
    return result


@router.post(
    "/wayback",
    response_model=WaybackLookupResponse,
    status_code=status.HTTP_200_OK,
    summary="Look up Wayback Machine capture history",
    description=(
        "Look up archived snapshots of a domain (or a specific page under it) via the "
        "Wayback Machine's CDX API"
    ),
)
@limiter.limit("30/minute")
async def wayback_lookup_post(
    request: Request, wayback_request: WaybackLookupRequest
) -> WaybackLookupResponse:
    """Perform a Wayback Machine lookup via POST request"""
    logger.info("POST Wayback lookup request - Domain: %s", wayback_request.domain)
    result = await perform_wayback_lookup(wayback_request)
    logger.info(
        "POST Wayback lookup completed - Domain: %s, Snapshots: %s",
        wayback_request.domain,
        result.total_snapshots,
    )
    return result


@router.get(
    "/wayback/{domain}",
    response_model=WaybackLookupResponse,
    status_code=status.HTTP_200_OK,
    summary="Look up Wayback Machine capture history via URL parameter",
    description=(
        "Query the Wayback Machine's CDX API using domain from URL path, optionally narrowed "
        "to a single page via the `path` query parameter"
    ),
)
@limiter.limit("30/minute")
async def wayback_lookup_get(
    request: Request, domain: str, path: str | None = None
) -> WaybackLookupResponse:
    """Perform a Wayback Machine lookup using domain from URL path via GET request"""
    logger.info("GET Wayback lookup request - Domain: %s, Path: %s", domain, path)
    wayback_request = WaybackLookupRequest(domain=domain, path=path)
    result = await perform_wayback_lookup(wayback_request)
    logger.info(
        "GET Wayback lookup completed - Domain: %s, Snapshots: %s", domain, result.total_snapshots
    )
    return result


@router.get(
    "/health",
    response_model=dict[str, Any],
    status_code=status.HTTP_200_OK,
    summary="Check domain lookup service health",
    description="Health check endpoint for the domain lookup service",
)
async def check_domain_service_health() -> dict[str, Any]:
    """Check if the domain lookup service is operational"""
    return {
        "service": "domain_lookup",
        "status": "healthy",
        "endpoints": [
            "/api/domain/lookup",
            "/api/domain/lookup/{domain}",
            "/api/domain/whois",
            "/api/domain/whois/{domain}",
            "/api/domain/ct-subdomains",
            "/api/domain/ct-subdomains/{domain}",
            "/api/domain/hackertarget-subdomains",
            "/api/domain/hackertarget-subdomains/{domain}",
            "/api/domain/rapiddns-subdomains",
            "/api/domain/rapiddns-subdomains/{domain}",
            "/api/domain/ssl-info",
            "/api/domain/ssl-info/{domain}",
            "/api/domain/security-headers",
            "/api/domain/security-headers/{domain}",
            "/api/domain/dnssec",
            "/api/domain/dnssec/{domain}",
            "/api/domain/blocklist",
            "/api/domain/blocklist/{domain}",
            "/api/domain/dns",
            "/api/domain/dns/{domain}",
            "/api/domain/dnsdumpster",
            "/api/domain/dnsdumpster/{domain}",
            "/api/domain/wayback",
            "/api/domain/wayback/{domain}",
        ],
    }
