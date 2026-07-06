import socket

import pytest

from app.core.security.ssrf_guard import (
    SSRFValidationError,
    resolve_validated_ip,
    validate_public_url,
)


def _fake_addrinfo(ip: str):
    family = socket.AF_INET6 if ":" in ip else socket.AF_INET
    sockaddr = (ip, 0, 0, 0) if family == socket.AF_INET6 else (ip, 0)
    return [(family, socket.SOCK_STREAM, 6, "", sockaddr)]


@pytest.mark.parametrize(
    "ip",
    [
        "127.0.0.1",  # loopback
        "169.254.169.254",  # cloud metadata / link-local
        "10.0.0.5",  # private
        "172.16.0.5",  # private
        "192.168.1.5",  # private
        "0.0.0.0",  # unspecified
        "::1",  # loopback (v6)
        "fe80::1",  # link-local (v6)
    ],
)
def test_resolve_validated_ip_rejects_non_public_addresses(monkeypatch, ip):
    monkeypatch.setattr(socket, "getaddrinfo", lambda *a, **k: _fake_addrinfo(ip))
    with pytest.raises(SSRFValidationError):
        resolve_validated_ip("evil.example.com")


def test_resolve_validated_ip_accepts_public_address(monkeypatch):
    monkeypatch.setattr(socket, "getaddrinfo", lambda *a, **k: _fake_addrinfo("93.184.216.34"))
    assert resolve_validated_ip("example.com") == "93.184.216.34"


def test_resolve_validated_ip_allow_private_override(monkeypatch):
    monkeypatch.setattr(socket, "getaddrinfo", lambda *a, **k: _fake_addrinfo("127.0.0.1"))
    assert resolve_validated_ip("localhost", allow_private=True) == "127.0.0.1"


def test_resolve_validated_ip_dns_failure(monkeypatch):
    def _raise(*_args, **_kwargs):
        raise socket.gaierror("no such host")

    monkeypatch.setattr(socket, "getaddrinfo", _raise)
    with pytest.raises(SSRFValidationError):
        resolve_validated_ip("nonexistent.invalid")


def test_validate_public_url_rejects_unsupported_scheme():
    with pytest.raises(SSRFValidationError):
        validate_public_url("file:///etc/passwd")


def test_validate_public_url_requires_host():
    with pytest.raises(SSRFValidationError):
        validate_public_url("http://")


def test_validate_public_url_returns_resolved_ip(monkeypatch):
    monkeypatch.setattr(socket, "getaddrinfo", lambda *a, **k: _fake_addrinfo("93.184.216.34"))
    assert validate_public_url("https://example.com/path") == "93.184.216.34"
