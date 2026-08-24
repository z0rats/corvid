import logging
from datetime import UTC, datetime
from typing import Any

from pydantic import BaseModel, Field, field_validator

logger = logging.getLogger(__name__)


def _validate_plain_domain(v: str) -> str:
    """Shared domain validator body: normalizes protocol/path/case and rejects search
    patterns (`*`/`?`), which none of this module's providers accept as input - each of
    the ones with their own wildcard concept (e.g. crt.sh's SAN matching) applies it
    server-side, not from user-supplied glob syntax."""
    if not v or not v.strip():
        raise ValueError("Domain cannot be empty")

    domain = v.strip().lower()

    if domain.startswith(("http://", "https://")):
        domain = domain.split("://", 1)[1]

    if "/" in domain:
        domain = domain.split("/", 1)[0]

    if len(domain) > 255:
        raise ValueError("Domain name too long")

    if any(char in domain for char in [" ", "\t", "\n", "\r", "*", "?"]):
        raise ValueError("Domain contains invalid characters")

    return domain


class DomainLookupRequest(BaseModel):
    """Request model for domain lookup operations"""

    domain: str = Field(
        ..., description="Domain name to lookup (e.g., 'example.com')", min_length=1, max_length=255
    )

    @field_validator("domain")
    @classmethod
    def validate_domain_format(cls, v: str) -> str:
        """Validate domain format and perform basic sanitization"""
        logger.debug("Schema validation for domain: '%s'", v)

        if not v or not v.strip():
            logger.warning("Empty domain provided in schema validation")
            raise ValueError("Domain cannot be empty")

        domain = v.strip().lower()

        if domain.startswith(("http://", "https://")):
            domain = domain.split("://", 1)[1]

        if "/" in domain:
            domain = domain.split("/", 1)[0]

        if len(domain) > 255:
            logger.error(
                "Domain too long in schema validation: '%s' (length: %s)", domain, len(domain)
            )
            raise ValueError("Domain name too long")

        if any(char in domain for char in [" ", "\t", "\n", "\r"]):
            logger.error("Invalid characters in domain: '%s'", domain)
            raise ValueError("Domain contains invalid characters")

        logger.debug("Schema validation successful: '%s' -> '%s'", v, domain)
        return domain


class UrlScanResult(BaseModel):
    """Individual URL scan result from urlscan.io API."""

    task: dict[str, Any] | None = Field(default=None, description="Task information from the scan")
    stats: dict[str, Any] | None = Field(default=None, description="Statistics from the scan")
    page: dict[str, Any] | None = Field(default=None, description="Page information from the scan")
    lists: dict[str, Any] | None = Field(
        default=None, description="Lists information from the scan"
    )
    verdicts: dict[str, Any] | None = Field(default=None, description="Verdicts from the scan")
    meta: dict[str, Any] | None = Field(default=None, description="Metadata from the scan")
    expanded: bool = Field(default=False, description="Whether the result is expanded in the UI")


class DomainLookupResponse(BaseModel):
    """Response model for domain lookup operations."""

    domain: str = Field(..., description="The domain that was looked up")
    results: list[UrlScanResult] = Field(..., description="List of scan results from urlscan.io")
    total_results: int = Field(..., description="Total number of results found", ge=0)
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        description="Timestamp when the lookup was performed",
    )


class DomainLookupError(BaseModel):
    """Error response model for domain lookup operations."""

    domain: str = Field(..., description="The domain that failed to be looked up")
    error_type: str = Field(..., description="Type of error that occurred")
    error_message: str = Field(..., description="Detailed error message")
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(UTC), description="Timestamp when the error occurred"
    )


class WhoisLookupRequest(BaseModel):
    """Request model for WHOIS/RDAP lookup operations"""

    domain: str = Field(
        ...,
        description="Domain name to look up via RDAP (e.g., 'example.com')",
        min_length=1,
        max_length=255,
    )

    @field_validator("domain")
    @classmethod
    def validate_domain_format(cls, v: str) -> str:
        """Validate domain format, rejecting search patterns which RDAP doesn't support"""
        if not v or not v.strip():
            raise ValueError("Domain cannot be empty")

        domain = v.strip().lower()

        if domain.startswith(("http://", "https://")):
            domain = domain.split("://", 1)[1]

        if "/" in domain:
            domain = domain.split("/", 1)[0]

        if len(domain) > 255:
            raise ValueError("Domain name too long")

        if any(char in domain for char in [" ", "\t", "\n", "\r", "*", "?"]):
            raise ValueError("Domain contains invalid characters")

        return domain


class CtSubdomainsRequest(BaseModel):
    """Request model for Certificate Transparency subdomain enumeration"""

    domain: str = Field(
        ...,
        description="Domain name to enumerate subdomains for via crt.sh (e.g., 'example.com')",
        min_length=1,
        max_length=255,
    )

    @field_validator("domain")
    @classmethod
    def validate_domain_format(cls, v: str) -> str:
        """Validate domain format, rejecting search patterns which crt.sh already applies itself"""
        if not v or not v.strip():
            raise ValueError("Domain cannot be empty")

        domain = v.strip().lower()

        if domain.startswith(("http://", "https://")):
            domain = domain.split("://", 1)[1]

        if "/" in domain:
            domain = domain.split("/", 1)[0]

        if len(domain) > 255:
            raise ValueError("Domain name too long")

        if any(char in domain for char in [" ", "\t", "\n", "\r", "*", "?"]):
            raise ValueError("Domain contains invalid characters")

        return domain


class CtCertificate(BaseModel):
    """A single Certificate Transparency log entry from crt.sh"""

    id: int | None = Field(default=None, description="crt.sh certificate/log entry ID")
    issuer_name: str | None = Field(default=None, description="Issuing CA name")
    common_name: str | None = Field(default=None, description="Certificate common name")
    name_value: str | None = Field(
        default=None, description="Newline-separated SAN entries as returned by crt.sh"
    )
    not_before: datetime | None = Field(default=None, description="Certificate validity start date")
    not_after: datetime | None = Field(default=None, description="Certificate validity end date")


class CtSubdomainsResponse(BaseModel):
    """Response model for Certificate Transparency subdomain enumeration"""

    domain: str = Field(..., description="The domain that was looked up")
    subdomains: list[str] = Field(
        default_factory=list, description="Deduplicated, sorted subdomains found in CT logs"
    )
    certificates: list[CtCertificate] = Field(
        default_factory=list, description="Certificate log entries backing the subdomain list"
    )
    total_certificates: int = Field(
        ..., description="Total number of certificate log entries found", ge=0
    )
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        description="Timestamp when the lookup was performed",
    )


class DnsLookupRequest(BaseModel):
    """Request model for DNS record lookup operations"""

    domain: str = Field(
        ...,
        description="Domain name to look up DNS records for (e.g., 'example.com')",
        min_length=1,
        max_length=255,
    )

    @field_validator("domain")
    @classmethod
    def validate_domain_format(cls, v: str) -> str:
        """Validate domain format, rejecting search patterns which DNS resolution doesn't support"""
        if not v or not v.strip():
            raise ValueError("Domain cannot be empty")

        domain = v.strip().lower()

        if domain.startswith(("http://", "https://")):
            domain = domain.split("://", 1)[1]

        if "/" in domain:
            domain = domain.split("/", 1)[0]

        if len(domain) > 255:
            raise ValueError("Domain name too long")

        if any(char in domain for char in [" ", "\t", "\n", "\r", "*", "?"]):
            raise ValueError("Domain contains invalid characters")

        return domain


class DnsRecordSet(BaseModel):
    """DNS records grouped by record type for a single lookup"""

    A: list[str] = Field(default_factory=list, description="IPv4 addresses")
    AAAA: list[str] = Field(default_factory=list, description="IPv6 addresses")
    MX: list[str] = Field(
        default_factory=list, description="Mail exchange records, preference-ordered"
    )
    TXT: list[str] = Field(default_factory=list, description="Text records")
    NS: list[str] = Field(default_factory=list, description="Authoritative nameservers")
    CNAME: list[str] = Field(default_factory=list, description="Canonical name records")


class DnsLookupResponse(BaseModel):
    """Response model for DNS record lookup operations"""

    domain: str = Field(..., description="The domain that was looked up")
    records: DnsRecordSet = Field(..., description="DNS records grouped by type")
    reverse_dns: dict[str, list[str]] = Field(
        default_factory=dict, description="PTR hostnames for each resolved A/AAAA IP address"
    )
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        description="Timestamp when the lookup was performed",
    )


class DnsDumpsterRequest(BaseModel):
    """Request model for DNSDumpster domain lookup operations"""

    domain: str = Field(
        ...,
        description="Domain name to look up via DNSDumpster (e.g., 'example.com')",
        min_length=1,
        max_length=255,
    )

    @field_validator("domain")
    @classmethod
    def validate_domain_format(cls, v: str) -> str:
        """Validate domain format, rejecting search patterns which DNSDumpster doesn't support"""
        if not v or not v.strip():
            raise ValueError("Domain cannot be empty")

        domain = v.strip().lower()

        if domain.startswith(("http://", "https://")):
            domain = domain.split("://", 1)[1]

        if "/" in domain:
            domain = domain.split("/", 1)[0]

        if len(domain) > 255:
            raise ValueError("Domain name too long")

        if any(char in domain for char in [" ", "\t", "\n", "\r", "*", "?"]):
            raise ValueError("Domain contains invalid characters")

        return domain


class DnsDumpsterBanner(BaseModel):
    """HTTP or HTTPS banner fingerprint for a single IP, as reported by DNSDumpster"""

    server: str | None = Field(default=None, description="Server header value")
    title: str | None = Field(default=None, description="Page title, if fetched")
    cn: str | None = Field(default=None, description="TLS certificate common name (HTTPS only)")
    apps: list[str] = Field(
        default_factory=list, description="Detected application/technology fingerprints"
    )


class DnsDumpsterIp(BaseModel):
    """A single resolved IP with ASN, geo, PTR, and banner detail from DNSDumpster"""

    ip: str | None = Field(default=None, description="Resolved IP address")
    asn: str | None = Field(default=None, description="Autonomous System Number")
    asn_name: str | None = Field(default=None, description="ASN organization/ISP name")
    asn_range: str | None = Field(default=None, description="ASN's advertised IP range")
    country: str | None = Field(default=None, description="Country name")
    country_code: str | None = Field(
        default=None, description="ISO country code, for flag rendering"
    )
    ptr: str | None = Field(default=None, description="Reverse DNS (PTR) hostname")
    banner_http: DnsDumpsterBanner | None = Field(
        default=None, description="HTTP banner fingerprint"
    )
    banner_https: DnsDumpsterBanner | None = Field(
        default=None, description="HTTPS banner fingerprint"
    )


class DnsDumpsterHost(BaseModel):
    """A single hostname with its resolved IPs, from a DNSDumpster record group (A/NS/MX/CNAME)"""

    host: str | None = Field(default=None, description="Hostname")
    ips: list[DnsDumpsterIp] = Field(default_factory=list, description="Resolved IPs for this host")


class DnsDumpsterResponse(BaseModel):
    """Response model for DNSDumpster domain lookup operations"""

    domain: str = Field(..., description="The domain that was looked up")
    a: list[DnsDumpsterHost] = Field(default_factory=list, description="Host (A) records")
    ns: list[DnsDumpsterHost] = Field(default_factory=list, description="Nameserver records")
    mx: list[DnsDumpsterHost] = Field(default_factory=list, description="Mail exchange records")
    cname: list[DnsDumpsterHost] = Field(default_factory=list, description="CNAME records")
    txt: list[str] = Field(default_factory=list, description="Text records")
    total_a_records: int = Field(
        default=0, description="Total number of A records reported by DNSDumpster"
    )
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        description="Timestamp when the lookup was performed",
    )


class WaybackLookupRequest(BaseModel):
    """Request model for Wayback Machine capture history lookup operations"""

    domain: str = Field(
        ...,
        description="Domain name to look up capture history for (e.g., 'example.com')",
        min_length=1,
        max_length=255,
    )
    path: str | None = Field(
        default=None,
        description=(
            "Optional path to narrow the query to a single page (e.g., '/login') instead of "
            "the whole domain"
        ),
        max_length=2000,
    )

    @field_validator("domain")
    @classmethod
    def validate_domain_format(cls, v: str) -> str:
        """Validate domain format, rejecting search patterns which CDX doesn't support"""
        if not v or not v.strip():
            raise ValueError("Domain cannot be empty")

        domain = v.strip().lower()

        if domain.startswith(("http://", "https://")):
            domain = domain.split("://", 1)[1]

        if "/" in domain:
            domain = domain.split("/", 1)[0]

        if len(domain) > 255:
            raise ValueError("Domain name too long")

        if any(char in domain for char in [" ", "\t", "\n", "\r", "*", "?"]):
            raise ValueError("Domain contains invalid characters")

        return domain

    @field_validator("path")
    @classmethod
    def validate_path_format(cls, v: str | None) -> str | None:
        """Normalize the optional path to start with a single leading slash"""
        if v is None or not v.strip():
            return None
        return "/" + v.strip().lstrip("/")


class WaybackSnapshot(BaseModel):
    """A single Wayback Machine capture from the CDX API"""

    timestamp: str = Field(..., description="Capture timestamp, CDX format (YYYYMMDDhhmmss)")
    original_url: str = Field(..., description="The captured URL, as recorded by CDX")
    status_code: str | None = Field(default=None, description="HTTP status code at capture time")
    mimetype: str | None = Field(default=None, description="Response MIME type at capture time")
    snapshot_url: str = Field(
        ..., description="Direct link to view this capture on web.archive.org"
    )


class WaybackLookupResponse(BaseModel):
    """Response model for Wayback Machine capture history lookup operations"""

    domain: str = Field(..., description="The domain that was looked up")
    total_snapshots: int = Field(..., description="Total number of captures found", ge=0)
    first_capture: datetime | None = Field(
        default=None, description="Timestamp of the earliest capture found"
    )
    last_capture: datetime | None = Field(
        default=None, description="Timestamp of the most recent capture found"
    )
    snapshots: list[WaybackSnapshot] = Field(
        default_factory=list, description="Captures found, oldest first"
    )
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        description="Timestamp when the lookup was performed",
    )


class WhoisEntity(BaseModel):
    """A single entity (registrar, registrant, admin, tech, ...) from an RDAP response"""

    role: str = Field(
        ..., description="Entity role, e.g. 'registrar', 'registrant', 'admin', 'tech'"
    )
    name: str | None = Field(default=None, description="Contact/organization full name")
    organization: str | None = Field(default=None, description="Organization name")
    email: str | None = Field(default=None, description="Contact email, if disclosed")


class WhoisLookupResponse(BaseModel):
    """Response model for WHOIS/RDAP lookup operations"""

    domain: str = Field(..., description="The domain that was looked up")
    rdap_server: str = Field(..., description="Authoritative RDAP server that answered the query")
    registrar: str | None = Field(default=None, description="Registrar name")
    registrar_iana_id: str | None = Field(default=None, description="Registrar IANA ID")
    creation_date: datetime | None = Field(default=None, description="Domain registration date")
    expiration_date: datetime | None = Field(default=None, description="Domain expiration date")
    updated_date: datetime | None = Field(default=None, description="Last update date")
    registrant_organization: str | None = Field(
        default=None, description="Registrant organization, if not redacted by a privacy proxy"
    )
    statuses: list[str] = Field(default_factory=list, description="EPP domain status codes")
    nameservers: list[str] = Field(default_factory=list, description="Authoritative nameservers")
    entities: list[WhoisEntity] = Field(
        default_factory=list, description="All disclosed entities from the RDAP record"
    )
    raw: dict[str, Any] = Field(
        default_factory=dict, description="Full raw RDAP response for advanced inspection"
    )
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        description="Timestamp when the lookup was performed",
    )


class HackerTargetSubdomainsRequest(BaseModel):
    """Request model for HackerTarget hostsearch subdomain enumeration"""

    domain: str = Field(
        ...,
        description="Domain name to enumerate subdomains for via HackerTarget's hostsearch "
        "API (e.g., 'example.com')",
        min_length=1,
        max_length=255,
    )

    @field_validator("domain")
    @classmethod
    def validate_domain_format(cls, v: str) -> str:
        return _validate_plain_domain(v)


class HackerTargetHost(BaseModel):
    """A single hostname/IP pair from HackerTarget's hostsearch API"""

    hostname: str = Field(..., description="Discovered hostname")
    ip_address: str | None = Field(default=None, description="Resolved IP address, if returned")


class HackerTargetSubdomainsResponse(BaseModel):
    """Response model for HackerTarget hostsearch subdomain enumeration"""

    domain: str = Field(..., description="The domain that was looked up")
    subdomains: list[str] = Field(
        default_factory=list, description="Deduplicated, sorted subdomains found"
    )
    hosts: list[HackerTargetHost] = Field(
        default_factory=list, description="Raw hostname/IP pairs as returned by HackerTarget"
    )
    total_hosts: int = Field(..., description="Total number of host entries found", ge=0)
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        description="Timestamp when the lookup was performed",
    )


class RapidDnsSubdomainsRequest(BaseModel):
    """Request model for RapidDNS subdomain enumeration"""

    domain: str = Field(
        ...,
        description="Domain name to enumerate subdomains for via RapidDNS (e.g., 'example.com')",
        min_length=1,
        max_length=255,
    )

    @field_validator("domain")
    @classmethod
    def validate_domain_format(cls, v: str) -> str:
        return _validate_plain_domain(v)


class RapidDnsRecord(BaseModel):
    """A single DNS record row from RapidDNS's subdomain lookup table"""

    hostname: str = Field(..., description="Discovered hostname")
    record_type: str = Field(..., description="DNS record type (A, AAAA, CNAME, NS, MX, ...)")
    address: str = Field(..., description="Resolved value for this record (IP, hostname, ...)")


class RapidDnsSubdomainsResponse(BaseModel):
    """Response model for RapidDNS subdomain enumeration"""

    domain: str = Field(..., description="The domain that was looked up")
    subdomains: list[str] = Field(
        default_factory=list, description="Deduplicated, sorted subdomains found"
    )
    records: list[RapidDnsRecord] = Field(
        default_factory=list, description="Raw DNS record rows as returned by RapidDNS"
    )
    total_records: int = Field(..., description="Total number of DNS record rows found", ge=0)
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        description="Timestamp when the lookup was performed",
    )


class SslInfoRequest(BaseModel):
    """Request model for TLS certificate inspection"""

    domain: str = Field(
        ...,
        description="Domain name to connect to on port 443 (e.g., 'example.com')",
        min_length=1,
        max_length=255,
    )

    @field_validator("domain")
    @classmethod
    def validate_domain_format(cls, v: str) -> str:
        return _validate_plain_domain(v)


class SslInfoResponse(BaseModel):
    """Response model for TLS certificate inspection"""

    domain: str = Field(..., description="The domain that was looked up")
    subject: str = Field(..., description="Certificate subject (RFC 4514 distinguished name)")
    issuer: str = Field(..., description="Certificate issuer (RFC 4514 distinguished name)")
    serial_number: str = Field(..., description="Certificate serial number, hex-encoded")
    not_before: datetime = Field(..., description="Certificate validity start date")
    not_after: datetime = Field(..., description="Certificate validity end date")
    days_until_expiry: int = Field(
        ..., description="Days remaining until expiry (negative if expired)"
    )
    is_expired: bool = Field(..., description="Whether the certificate has already expired")
    hostname_matches: bool = Field(
        ..., description="Whether the requested domain is covered by the certificate's SAN entries"
    )
    subject_alt_names: list[str] = Field(
        default_factory=list,
        description="DNS names from the certificate's Subject Alternative Name",
    )
    tls_version: str | None = Field(default=None, description="Negotiated TLS protocol version")
    cipher: str | None = Field(default=None, description="Negotiated cipher suite name")
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        description="Timestamp when the lookup was performed",
    )


class SecurityHeadersRequest(BaseModel):
    """Request model for security response-header audit"""

    domain: str = Field(
        ...,
        description="Domain name to fetch over HTTPS and inspect response headers for "
        "(e.g., 'example.com')",
        min_length=1,
        max_length=255,
    )

    @field_validator("domain")
    @classmethod
    def validate_domain_format(cls, v: str) -> str:
        return _validate_plain_domain(v)


class HstsInfo(BaseModel):
    """Parsed Strict-Transport-Security header directives"""

    max_age: int | None = Field(default=None, description="max-age directive, in seconds")
    include_subdomains: bool = Field(default=False, description="Whether includeSubDomains was set")
    preload: bool = Field(default=False, description="Whether preload was set")
    raw_value: str = Field(..., description="The raw header value")


class SecurityHeadersResponse(BaseModel):
    """Response model for security response-header audit"""

    domain: str = Field(..., description="The domain that was looked up")
    status_code: int = Field(..., description="HTTP status code of the final response")
    present_headers: dict[str, str] = Field(
        default_factory=dict, description="Security headers found, label to raw value"
    )
    missing_headers: list[str] = Field(
        default_factory=list, description="Security headers not present in the response"
    )
    hsts: HstsInfo | None = Field(
        default=None, description="Parsed HSTS directives, if the header was present"
    )
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        description="Timestamp when the lookup was performed",
    )


class DnssecRequest(BaseModel):
    """Request model for the DNSSEC signal check"""

    domain: str = Field(
        ...,
        description="Domain name to check for published DNSKEY/DS records (e.g., 'example.com')",
        min_length=1,
        max_length=255,
    )

    @field_validator("domain")
    @classmethod
    def validate_domain_format(cls, v: str) -> str:
        return _validate_plain_domain(v)


class DnssecResponse(BaseModel):
    """Response model for the DNSSEC signal check"""

    domain: str = Field(..., description="The domain that was looked up")
    dnssec_enabled: bool = Field(
        ..., description="Whether the domain publishes a DNSKEY or DS record"
    )
    dnskey_records: list[str] = Field(default_factory=list, description="Raw DNSKEY records found")
    ds_records: list[str] = Field(default_factory=list, description="Raw DS records found")
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        description="Timestamp when the lookup was performed",
    )


class BlocklistRequest(BaseModel):
    """Request model for the DNS-sinkhole/blocklist check"""

    domain: str = Field(
        ...,
        description="Domain name to check against public security-filtering DNS resolvers "
        "(e.g., 'example.com')",
        min_length=1,
        max_length=255,
    )

    @field_validator("domain")
    @classmethod
    def validate_domain_format(cls, v: str) -> str:
        return _validate_plain_domain(v)


class BlocklistProviderResult(BaseModel):
    """One provider's filtered-vs-baseline DNS answer for the blocklist check"""

    provider: str = Field(..., description="Name of the DNS provider/resolver tier")
    blocked: bool = Field(
        ..., description="Whether the filtered resolver's answer differs from the baseline"
    )
    filtered_answer: list[str] = Field(
        default_factory=list, description="A records returned by the provider's filtering resolver"
    )
    baseline_answer: list[str] = Field(
        default_factory=list, description="A records returned by the provider's plain resolver"
    )


class BlocklistResponse(BaseModel):
    """Response model for the DNS-sinkhole/blocklist check"""

    domain: str = Field(..., description="The domain that was looked up")
    results: list[BlocklistProviderResult] = Field(
        default_factory=list, description="Per-provider results"
    )
    flagged_count: int = Field(..., description="Number of providers that flagged the domain", ge=0)
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        description="Timestamp when the lookup was performed",
    )
