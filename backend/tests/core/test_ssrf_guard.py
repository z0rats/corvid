import asyncio
import socket

import httpx
import pytest

from app.core.security.ssrf_guard import (
    SSRFValidationError,
    resolve_validated_ip,
    safe_get,
    validate_public_url,
)


def _fake_addrinfo(ip: str):
    family = socket.AF_INET6 if ":" in ip else socket.AF_INET
    sockaddr = (ip, 0, 0, 0) if family == socket.AF_INET6 else (ip, 0)
    return [(family, socket.SOCK_STREAM, 6, "", sockaddr)]


def _fake_getaddrinfo_for(host_to_ip: dict[str, str]):
    """Returns a `socket.getaddrinfo` stand-in resolving each host in the map
    to its configured IP, and raising `gaierror` for any other host."""

    def _getaddrinfo(host, *_args, **_kwargs):
        if host not in host_to_ip:
            raise socket.gaierror(f"no such host: {host}")
        return _fake_addrinfo(host_to_ip[host])

    return _getaddrinfo


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


# --- safe_get --------------------------------------------------------------
#
# safe_get is the SSRF-critical entrypoint: it must connect to the resolved
# IP (not let the transport re-resolve the hostname), send the original
# hostname as the Host header, and re-run the same public-IP validation on
# every redirect hop before following it - a redirect to an internal target
# must be rejected before any request reaches it.


def _run(coro):
    return asyncio.run(coro)


class TestSafeGet:
    def test_pins_request_to_the_resolved_ip_and_sets_host_header(self, monkeypatch):
        monkeypatch.setattr(
            socket, "getaddrinfo", _fake_getaddrinfo_for({"public.example.com": "93.184.216.34"})
        )
        seen_requests = []

        def handler(request: httpx.Request) -> httpx.Response:
            seen_requests.append(request)
            return httpx.Response(200, json={"ok": True})

        async def _call():
            async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
                return await safe_get(client, "https://public.example.com/path?x=1")

        response = _run(_call())

        assert response.status_code == 200
        assert len(seen_requests) == 1
        sent = seen_requests[0]
        assert sent.url.host == "93.184.216.34"
        assert sent.url.path == "/path"
        assert sent.headers["host"] == "public.example.com"

    def test_merges_caller_supplied_headers_with_the_host_override(self, monkeypatch):
        monkeypatch.setattr(
            socket, "getaddrinfo", _fake_getaddrinfo_for({"public.example.com": "93.184.216.34"})
        )
        seen_requests = []

        def handler(request: httpx.Request) -> httpx.Response:
            seen_requests.append(request)
            return httpx.Response(200)

        async def _call():
            async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
                await safe_get(client, "https://public.example.com/", headers={"X-Custom": "value"})

        _run(_call())

        assert seen_requests[0].headers["x-custom"] == "value"
        assert seen_requests[0].headers["host"] == "public.example.com"

    def test_rejects_a_target_that_resolves_to_a_private_address(self, monkeypatch):
        monkeypatch.setattr(
            socket, "getaddrinfo", _fake_getaddrinfo_for({"internal.example.com": "10.0.0.5"})
        )

        def handler(request: httpx.Request) -> httpx.Response:
            raise AssertionError("request must not reach the transport for a private target")

        async def _call():
            async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
                await safe_get(client, "http://internal.example.com/")

        with pytest.raises(SSRFValidationError):
            _run(_call())

    def test_follows_a_redirect_and_revalidates_the_new_host(self, monkeypatch):
        monkeypatch.setattr(
            socket,
            "getaddrinfo",
            _fake_getaddrinfo_for(
                {"first.example.com": "93.184.216.34", "second.example.com": "1.1.1.1"}
            ),
        )
        seen_requests = []

        def handler(request: httpx.Request) -> httpx.Response:
            seen_requests.append(request)
            if request.url.host == "93.184.216.34":
                return httpx.Response(302, headers={"location": "https://second.example.com/final"})
            return httpx.Response(200, json={"done": True})

        async def _call():
            async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
                return await safe_get(client, "https://first.example.com/start")

        response = _run(_call())

        assert response.status_code == 200
        assert response.json() == {"done": True}
        assert len(seen_requests) == 2
        assert seen_requests[0].url.host == "93.184.216.34"
        assert seen_requests[1].url.host == "1.1.1.1"
        assert seen_requests[1].headers["host"] == "second.example.com"

    def test_rejects_a_redirect_to_a_private_address_without_following_it(self, monkeypatch):
        monkeypatch.setattr(
            socket,
            "getaddrinfo",
            _fake_getaddrinfo_for(
                {"first.example.com": "93.184.216.34", "internal.example.com": "10.0.0.9"}
            ),
        )
        seen_requests = []

        def handler(request: httpx.Request) -> httpx.Response:
            seen_requests.append(request)
            assert request.url.host != "10.0.0.9", (
                "must never connect to the private redirect target"
            )
            return httpx.Response(302, headers={"location": "http://internal.example.com/admin"})

        async def _call():
            async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
                await safe_get(client, "https://first.example.com/start")

        with pytest.raises(SSRFValidationError):
            _run(_call())

        # Only the first (public) hop was ever actually requested.
        assert len(seen_requests) == 1

    def test_raises_after_exceeding_max_redirects(self, monkeypatch):
        monkeypatch.setattr(
            socket, "getaddrinfo", _fake_getaddrinfo_for({"loop.example.com": "93.184.216.34"})
        )

        def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(302, headers={"location": "https://loop.example.com/next"})

        async def _call():
            async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
                await safe_get(client, "https://loop.example.com/start", max_redirects=2)

        with pytest.raises(SSRFValidationError, match="Too many redirects"):
            _run(_call())
