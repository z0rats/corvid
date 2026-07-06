"""SSRF guard: validate that outbound requests don't target internal/private network addresses.

Use this whenever server code fetches a URL that was supplied (directly or indirectly)
by the user, e.g. a feed URL for favicon discovery. Without it, an attacker-controlled
URL could make the server reach cloud metadata endpoints (169.254.169.254), other
services on the internal docker network, or localhost-only admin interfaces.
"""
import ipaddress
import socket
from urllib.parse import urlsplit


class SSRFValidationError(Exception):
    """Raised when a URL/hostname resolves to a non-public network address."""


def _is_disallowed_ip(ip: str) -> bool:
    addr = ipaddress.ip_address(ip)
    return (
        addr.is_private
        or addr.is_loopback
        or addr.is_link_local
        or addr.is_multicast
        or addr.is_reserved
        or addr.is_unspecified
    )


def resolve_validated_ip(hostname: str, *, allow_private: bool = False) -> str:
    """Resolve `hostname` and return the first IP address that is safe to connect to.

    Resolving (rather than trusting the hostname string) and validating the actual
    IP is what defeats DNS-rebinding: callers should connect to the IP returned
    here instead of letting the HTTP client re-resolve the hostname later.
    """
    try:
        infos = socket.getaddrinfo(hostname, None)
    except socket.gaierror as e:
        raise SSRFValidationError(f"Could not resolve host: {hostname}") from e

    for _family, _type, _proto, _canonname, sockaddr in infos:
        ip = sockaddr[0]
        if allow_private or not _is_disallowed_ip(ip):
            return ip

    raise SSRFValidationError(f"Host '{hostname}' resolves only to non-public addresses")


def validate_public_url(url: str, *, allow_private: bool = False) -> str:
    """Validate that `url`'s host resolves to a public address.

    Returns the validated IP so the caller can pin the actual connection to it
    (see `favicon_downloader._safe_get` for an example) rather than re-resolving
    the hostname at request time.
    """
    parsed = urlsplit(url)
    if parsed.scheme not in ("http", "https"):
        raise SSRFValidationError(f"Unsupported URL scheme: {parsed.scheme!r}")
    if not parsed.hostname:
        raise SSRFValidationError(f"URL has no host: {url}")
    return resolve_validated_ip(parsed.hostname, allow_private=allow_private)
