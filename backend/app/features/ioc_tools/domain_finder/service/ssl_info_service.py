"""
TLS certificate chain inspection via a direct handshake - stdlib `ssl` +
`socket`, no external service or API key.

The domain is a user-supplied connection target (not a query parameter
against a fixed host, unlike the rest of domain_finder's keyless checks), so
the connection is pinned to an `ssrf_guard`-validated IP first, the same
primitive `rdap_api_service.py` uses via `safe_get`. Certificate *verification*
is deliberately disabled (`CERT_NONE`): an analyst investigating a suspicious
domain often specifically wants to see a self-signed, expired, or
hostname-mismatched certificate, which a verifying handshake would refuse to
complete at all. The raw DER bytes are parsed with `cryptography` (already an
installed dependency, pulled in for `secrets_crypto.py`'s Fernet key handling),
not the stdlib `ssl.getpeercert()` dict form, since that form is only
populated for a verified connection.
"""

import asyncio
import logging
import socket
import ssl
from datetime import UTC, datetime
from typing import Any

from cryptography import x509

from app.core.config.settings import settings
from app.core.exceptions import AppHTTPException
from app.core.security.ssrf_guard import SSRFValidationError, resolve_validated_ip
from app.features.ioc_tools.domain_finder.schemas.domain_schemas import (
    SslInfoRequest,
    SslInfoResponse,
)

logger = logging.getLogger(__name__)

SSL_PORT = 443
SSL_CONNECT_TIMEOUT = 10.0


def _fetch_certificate_sync(domain: str, ip: str) -> dict[str, Any]:
    """Blocking TLS handshake + certificate fetch - `ssl`/`socket` have no native
    asyncio API for this, so the caller runs it via `asyncio.to_thread`."""
    context = ssl.create_default_context()
    context.check_hostname = False
    context.verify_mode = ssl.CERT_NONE

    with socket.create_connection((ip, SSL_PORT), timeout=SSL_CONNECT_TIMEOUT) as sock:
        with context.wrap_socket(sock, server_hostname=domain) as tls_sock:
            der_cert = tls_sock.getpeercert(binary_form=True)
            cipher = tls_sock.cipher()
            tls_version = tls_sock.version()

    if der_cert is None:
        raise ssl.SSLError("Server presented no certificate")

    cert = x509.load_der_x509_certificate(der_cert)
    return {
        "subject": cert.subject.rfc4514_string(),
        "issuer": cert.issuer.rfc4514_string(),
        "serial_number": format(cert.serial_number, "x"),
        "not_before": cert.not_valid_before_utc,
        "not_after": cert.not_valid_after_utc,
        "subject_alt_names": _extract_san(cert),
        "cipher": cipher[0] if cipher else None,
        "tls_version": tls_version,
    }


def _extract_san(cert: x509.Certificate) -> list[str]:
    try:
        ext = cert.extensions.get_extension_for_class(x509.SubjectAlternativeName)
        return list(ext.value.get_values_for_type(x509.DNSName))
    except x509.ExtensionNotFound:
        return []


def _hostname_matches(domain: str, san_entries: list[str]) -> bool:
    """Check `domain` against SAN entries, honoring a single leading `*.` wildcard
    the way browsers do (matches exactly one label, not sub-subdomains)."""
    domain = domain.lower()
    for entry in san_entries:
        entry = entry.lower()
        if entry == domain:
            return True
        if entry.startswith("*."):
            suffix = entry[1:]  # keep the leading dot, e.g. ".example.com"
            if domain.endswith(suffix) and domain.count(".") == entry.count("."):
                return True
    return False


async def perform_ssl_info_lookup(request: SslInfoRequest) -> SslInfoResponse:
    """
    Fetch and parse the TLS certificate a domain presents on port 443.

    Args:
        request: Validated SSL info request

    Returns:
        SslInfoResponse containing the parsed certificate and connection details

    Raises:
        AppHTTPException: For SSRF validation failures, connection/handshake failures
    """
    domain = request.domain
    logger.info("Starting SSL info lookup for: %s", domain)

    try:
        ip = resolve_validated_ip(
            domain, allow_private=settings.security.allow_private_network_targets
        )
    except SSRFValidationError as e:
        logger.warning("SSRF validation failed for SSL info lookup on %s: %s", domain, e)
        raise AppHTTPException(
            status_code=400, detail=str(e), error_code="SSL_INFO_INVALID_HOST"
        ) from e

    try:
        raw = await asyncio.to_thread(_fetch_certificate_sync, domain, ip)
    except TimeoutError as e:
        logger.error("Timeout during SSL handshake with %s: %s", domain, e)
        raise AppHTTPException(
            status_code=504,
            detail="Connection timed out during TLS handshake",
            error_code="SSL_INFO_TIMEOUT",
        ) from e
    except (ssl.SSLError, OSError) as e:
        logger.error("Failed to establish TLS connection to %s: %s", domain, e)
        raise AppHTTPException(
            status_code=502,
            detail=f"Could not establish a TLS connection: {e}",
            error_code="SSL_INFO_CONNECTION_ERROR",
        ) from e
    except Exception as e:
        logger.error("Unexpected error fetching SSL info for %s: %s", domain, e, exc_info=True)
        raise AppHTTPException(
            status_code=500,
            detail="An unexpected error occurred while fetching SSL info",
            error_code="SSL_INFO_UNEXPECTED_ERROR",
        ) from e

    now = datetime.now(UTC)
    days_until_expiry = (raw["not_after"] - now).days

    response = SslInfoResponse(
        domain=domain,
        subject=raw["subject"],
        issuer=raw["issuer"],
        serial_number=raw["serial_number"],
        not_before=raw["not_before"],
        not_after=raw["not_after"],
        days_until_expiry=days_until_expiry,
        is_expired=raw["not_after"] < now,
        hostname_matches=_hostname_matches(domain, raw["subject_alt_names"]),
        subject_alt_names=raw["subject_alt_names"],
        tls_version=raw["tls_version"],
        cipher=raw["cipher"],
    )
    logger.info(
        "SSL info lookup completed for %s - issuer=%s, expires_in=%s days",
        domain,
        response.issuer,
        days_until_expiry,
    )
    return response
