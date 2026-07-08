"""SSRF guard: validate that outbound requests don't target internal/private network addresses.

Use this whenever server code fetches a URL that was supplied (directly or indirectly)
by the user, e.g. a feed URL for favicon discovery. Without it, an attacker-controlled
URL could make the server reach cloud metadata endpoints (169.254.169.254), other
services on the internal docker network, or localhost-only admin interfaces.
"""
import ipaddress
import socket
from urllib.parse import urlsplit, urlunsplit, urljoin

import httpx


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


async def safe_get(
    client: httpx.AsyncClient,
    url: str,
    *,
    allow_private: bool = False,
    max_redirects: int = 5,
    **kwargs,
) -> httpx.Response:
    """SSRF-safe GET: validates and pins every request to a vetted public IP.

    Redirects are followed manually (up to `max_redirects`), re-validating and
    re-pinning each hop. Pass a client configured with `follow_redirects=False`:
    httpx's own redirect handling would re-resolve the `Location` header's host
    without going through this validation, reopening the SSRF/DNS-rebinding gap
    this function exists to close.
    """
    extra_headers = kwargs.pop("headers", None) or {}
    for _ in range(max_redirects + 1):
        parsed = urlsplit(url)
        ip = validate_public_url(url, allow_private=allow_private)
        pinned_host = f"[{ip}]" if ":" in ip else ip
        pinned_netloc = f"{pinned_host}:{parsed.port}" if parsed.port else pinned_host
        pinned_url = urlunsplit((parsed.scheme, pinned_netloc, parsed.path or "/", parsed.query, parsed.fragment))
        extensions = {"sni_hostname": parsed.hostname} if parsed.scheme == "https" else {}
        headers = {**extra_headers, "Host": parsed.hostname}
        response = await client.get(pinned_url, headers=headers, extensions=extensions, **kwargs)
        if response.is_redirect and response.has_redirect_location:
            url = urljoin(url, response.headers["location"])
            continue
        return response
    raise SSRFValidationError(f"Too many redirects while fetching {url}")
