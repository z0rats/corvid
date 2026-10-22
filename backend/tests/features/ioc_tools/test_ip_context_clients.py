"""check_ip_geo (ipapi.is) and check_ip_rdap (rdap.org bootstrap): reserved addresses never
leave the backend, a 404 from RDAP is "not found" rather than an error, and the RDAP parser
finds the abuse contact whether a registry nests it (ARIN) or lists it top-level (RIPE)."""

import socket

import httpx
import pytest

from app.core.external_sources.contract import SourceDriftError
from app.core.security import ssrf_guard
from app.core.security.ssrf_guard import SSRFValidationError
from app.features.ioc_tools.ioc_lookup.single_lookup.service import ip_context_clients
from app.features.ioc_tools.ioc_lookup.single_lookup.service.client_base import (
    ServiceRateLimitError,
    ServiceUnavailableError,
)
from tests.conftest import run as _run


def _response(status_code: int, json=None, host: str = "api.ipapi.is") -> httpx.Response:
    request = httpx.Request("GET", "https://203.0.113.1/x", headers={"Host": host})
    return httpx.Response(status_code, request=request, json=json if json is not None else {})


class _FakeClient:
    def __init__(self, response: httpx.Response):
        self._response = response
        self.calls: list[dict] = []

    async def get(self, url, **kwargs):
        self.calls.append({"url": url, **kwargs})
        return self._response


def _patch_client(monkeypatch, response: httpx.Response) -> _FakeClient:
    fake = _FakeClient(response)
    monkeypatch.setattr(ip_context_clients, "get_client", lambda: fake)
    return fake


def _patch_safe_get(monkeypatch, response=None, exc=None) -> list[str]:
    urls: list[str] = []

    async def fake_safe_get(client, url, **kwargs):
        urls.append(url)
        if exc is not None:
            raise exc
        return response

    monkeypatch.setattr(ip_context_clients, "safe_get", fake_safe_get)
    return urls


@pytest.mark.parametrize(
    "ip",
    ["10.0.0.1", "192.168.1.1", "127.0.0.1", "100.64.0.1", "169.254.1.1", "::1", "fd00::1", "x"],
)
def test_non_public_addresses_are_reserved(ip):
    assert ip_context_clients.is_reserved_ip(ip) is True


@pytest.mark.parametrize("ip", ["1.1.1.1", "193.0.6.139", "2606:4700:4700::1111"])
def test_public_addresses_are_not_reserved(ip):
    assert ip_context_clients.is_reserved_ip(ip) is False


# --- check_ip_geo ----------------------------------------------------------------------------

_IPAPI_HIT = {
    "ip": "1.1.1.1",
    "is_bogon": False,
    "company": "APNIC Research and Development",
    "asn": "AS13335 Cloudflare, Inc.",
    "city": "Brisbane",
    "region": "Queensland",
    "country": "Australia",
    "lat": -27.46,
    "lon": 153.02,
    "timezone": "Australia/Brisbane",
    "docs": "https://ipapi.is/free-tier.html",
}


class TestCheckIpGeo:
    def test_queries_ipapi_and_keeps_the_card_fields(self, monkeypatch):
        fake = _patch_client(monkeypatch, _response(200, json=_IPAPI_HIT))

        result = _run(ip_context_clients.check_ip_geo("1.1.1.1"))

        assert fake.calls[0]["url"] == "https://api.ipapi.is/"
        assert fake.calls[0]["params"] == {"q": "1.1.1.1"}
        assert result["reserved"] is False
        assert result["asn"] == "AS13335 Cloudflare, Inc."
        assert result["country"] == "Australia"
        assert "docs" not in result

    def test_a_reserved_address_is_answered_without_a_request(self, monkeypatch):
        fake = _patch_client(monkeypatch, _response(500))

        result = _run(ip_context_clients.check_ip_geo("192.168.0.10"))

        assert fake.calls == []
        assert result["reserved"] is True
        assert result["country"] is None

    def test_a_bogon_answer_is_reported_as_reserved(self, monkeypatch):
        _patch_client(monkeypatch, _response(200, json={**_IPAPI_HIT, "is_bogon": True}))

        assert _run(ip_context_clients.check_ip_geo("1.1.1.1"))["reserved"] is True

    def test_a_missing_field_is_drift(self, monkeypatch):
        body = {k: v for k, v in _IPAPI_HIT.items() if k != "asn"}
        _patch_client(monkeypatch, _response(200, json=body))

        with pytest.raises(SourceDriftError):
            _run(ip_context_clients.check_ip_geo("1.1.1.1"))

    def test_429_is_rate_limited(self, monkeypatch):
        _patch_client(monkeypatch, _response(429))

        with pytest.raises(ServiceRateLimitError):
            _run(ip_context_clients.check_ip_geo("1.1.1.1"))


# --- check_ip_rdap ---------------------------------------------------------------------------


def _vcard(**props):
    return ["vcard", [[name, {}, "text", value] for name, value in props.items()]]


_RIPE_NETWORK = {
    "objectClassName": "ip network",
    "handle": "193.0.0.0 - 193.0.7.255",
    "name": "RIPE-NCC",
    "type": "ASSIGNED PA",
    "startAddress": "193.0.0.0",
    "endAddress": "193.0.7.255",
    "country": "NL",
    "cidr0_cidrs": [{"v4prefix": "193.0.0.0", "length": 21}],
    "entities": [
        {"roles": ["registrant"], "vcardArray": _vcard(fn="RIPE Network Coordination Centre")},
        {"roles": ["abuse"], "vcardArray": _vcard(fn="Abuse", email="abuse@ripe.net")},
    ],
    "events": [
        {"eventAction": "registration", "eventDate": "2003-03-17T12:15:57Z"},
        {"eventAction": "last changed", "eventDate": "2026-03-19T09:08:35Z"},
    ],
}

_ARIN_NETWORK = {
    "objectClassName": "ip network",
    "handle": "NET6-2606-4700-1",
    "name": "CLOUDFLARENET",
    "startAddress": "2606:4700::",
    "endAddress": "2606:4700:ffff:ffff:ffff:ffff:ffff:ffff",
    "cidr0_cidrs": [{"v6prefix": "2606:4700::", "length": 32}],
    "entities": [
        {
            "roles": ["registrant"],
            "vcardArray": _vcard(fn="Cloudflare, Inc."),
            "entities": [
                {"roles": ["abuse"], "vcardArray": _vcard(fn="Abuse", email="abuse@cloudflare.com")}
            ],
        }
    ],
}


class TestCheckIpRdap:
    def test_goes_through_the_bootstrap_and_records_the_answering_registry(self, monkeypatch):
        urls = _patch_safe_get(
            monkeypatch, _response(200, json=_RIPE_NETWORK, host="rdap.db.ripe.net")
        )

        result = _run(ip_context_clients.check_ip_rdap("193.0.6.139"))

        assert urls == ["https://rdap.org/ip/193.0.6.139"]
        assert result["registry"] == "RIPE NCC"
        assert result["registry_server"] == "rdap.db.ripe.net"
        assert result["found"] is True
        assert result["name"] == "RIPE-NCC"
        assert result["cidrs"] == ["193.0.0.0/21"]
        assert result["registrant"] == "RIPE Network Coordination Centre"
        assert result["abuse_emails"] == ["abuse@ripe.net"]
        assert result["registration"] == "2003-03-17T12:15:57Z"
        assert result["last_changed"] == "2026-03-19T09:08:35Z"

    def test_finds_an_abuse_contact_nested_under_the_registrant(self, monkeypatch):
        _patch_safe_get(monkeypatch, _response(200, json=_ARIN_NETWORK, host="rdap.arin.net"))

        result = _run(ip_context_clients.check_ip_rdap("2606:4700:4700::1111"))

        assert result["registry"] == "ARIN"
        assert result["registry_server"] == "rdap.arin.net"
        assert result["cidrs"] == ["2606:4700::/32"]
        assert result["registrant"] == "Cloudflare, Inc."
        assert result["abuse_emails"] == ["abuse@cloudflare.com"]

    def test_a_reserved_address_is_answered_without_a_request(self, monkeypatch):
        urls = _patch_safe_get(monkeypatch, _response(500))

        result = _run(ip_context_clients.check_ip_rdap("10.0.0.1"))

        assert urls == []
        assert result == {**result, "reserved": True, "found": False, "abuse_emails": []}

    def test_404_is_not_found_not_an_error(self, monkeypatch):
        _patch_safe_get(monkeypatch, _response(404, host="rdap.org"))

        result = _run(ip_context_clients.check_ip_rdap("1.1.1.1"))

        assert result["found"] is False
        assert result["reserved"] is False
        assert result["cidrs"] == []

    def test_a_body_that_is_not_an_rdap_object_is_drift(self, monkeypatch):
        _patch_safe_get(monkeypatch, _response(200, json={"handle": "x"}))

        with pytest.raises(SourceDriftError):
            _run(ip_context_clients.check_ip_rdap("1.1.1.1"))

    def test_an_unknown_registry_host_keeps_the_server_but_no_rir_name(self, monkeypatch):
        _patch_safe_get(monkeypatch, _response(200, json=_RIPE_NETWORK, host="rdap.example.net"))

        result = _run(ip_context_clients.check_ip_rdap("193.0.6.139"))

        assert result["registry"] is None
        assert result["registry_server"] == "rdap.example.net"

    def test_a_timeout_reaches_the_engine_as_a_timeout(self, monkeypatch):
        _patch_safe_get(monkeypatch, exc=httpx.ReadTimeout("slow"))

        with pytest.raises(httpx.TimeoutException):
            _run(ip_context_clients.check_ip_rdap("1.1.1.1"))

    @pytest.mark.parametrize(
        "exc", [httpx.ConnectError("refused"), SSRFValidationError("redirect to a private host")]
    )
    def test_a_connection_or_redirect_failure_is_unavailable(self, monkeypatch, exc):
        _patch_safe_get(monkeypatch, exc=exc)

        with pytest.raises(ServiceUnavailableError):
            _run(ip_context_clients.check_ip_rdap("1.1.1.1"))


# --- the bootstrap redirect through the real `safe_get` --------------------------------------

# Public stand-in addresses for the hosts involved; `safe_get` pins each hop to what DNS says.
_FAKE_DNS = {
    "rdap.org": "104.16.0.10",
    "rdap.db.ripe.net": "193.0.6.140",
    "rdap.arin.net": "199.71.0.10",
    "internal.example": "10.0.0.5",
}
_REGISTRY_FOR_IP = {"193.0.6.139": "rdap.db.ripe.net", "2606:4700:4700::1111": "rdap.arin.net"}
_NETWORK_BY_REGISTRY = {"rdap.db.ripe.net": _RIPE_NETWORK, "rdap.arin.net": _ARIN_NETWORK}


def _route_rdap(redirect_to=None):
    """A transport standing in for rdap.org and two RIRs: rdap.org answers 302 to the
    registry for the IP (or `redirect_to`), each registry answers its network object."""

    def handler(request: httpx.Request) -> httpx.Response:
        host = request.headers["host"]
        ip = request.url.path.rsplit("/", 1)[-1]
        if host == "rdap.org":
            target = redirect_to or f"https://{_REGISTRY_FOR_IP[ip]}/ip/{ip}"
            return httpx.Response(302, headers={"location": target})
        return httpx.Response(200, json=_NETWORK_BY_REGISTRY[host])

    return handler


@pytest.fixture
def rdap_network(monkeypatch):
    def fake_getaddrinfo(host, *args, **kwargs):
        return [(socket.AF_INET, socket.SOCK_STREAM, 6, "", (_FAKE_DNS[host], 0))]

    monkeypatch.setattr(ssrf_guard.socket, "getaddrinfo", fake_getaddrinfo)
    real_client = httpx.AsyncClient

    def install(redirect_to=None):
        transport = httpx.MockTransport(_route_rdap(redirect_to))
        monkeypatch.setattr(
            ip_context_clients.httpx,
            "AsyncClient",
            lambda **kwargs: real_client(transport=transport, **kwargs),
        )

    return install


@pytest.mark.parametrize(
    ("ip", "registry", "server"),
    [
        ("193.0.6.139", "RIPE NCC", "rdap.db.ripe.net"),
        ("2606:4700:4700::1111", "ARIN", "rdap.arin.net"),
    ],
)
def test_the_bootstrap_redirect_lands_on_the_right_registry(rdap_network, ip, registry, server):
    rdap_network()

    result = _run(ip_context_clients.check_ip_rdap(ip))

    assert result["registry"] == registry
    assert result["registry_server"] == server


def test_a_redirect_to_an_internal_host_is_refused(rdap_network):
    rdap_network(redirect_to="https://internal.example/ip/1.1.1.1")

    with pytest.raises(ServiceUnavailableError):
        _run(ip_context_clients.check_ip_rdap("1.1.1.1"))
