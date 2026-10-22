"""check_censys: host lookup for IPs, web property 443 -> 80 for domains, actionable messages
for a bad token and a paid-only endpoint, 404 as "not found", and a trimmed result."""

import httpx
import pytest

from app.core.external_sources.contract import SourceDriftError
from app.features.ioc_tools.ioc_lookup.single_lookup.service import censys_client
from app.features.ioc_tools.ioc_lookup.single_lookup.service.client_base import (
    ServiceAuthError,
    ServiceError,
)
from tests.conftest import run as _run


def _response(status_code: int, json=None, text: str | None = None) -> httpx.Response:
    request = httpx.Request("GET", "https://api.platform.censys.io/v3/global/asset/x")
    if text is not None:
        return httpx.Response(status_code, request=request, text=text)
    return httpx.Response(status_code, request=request, json=json if json is not None else {})


class _FakeClient:
    """Answers each GET from `responses` in order."""

    def __init__(self, *responses: httpx.Response):
        self._responses = list(responses)
        self.calls: list[dict] = []

    async def get(self, url, **kwargs):
        self.calls.append({"url": url, **kwargs})
        return self._responses.pop(0)


def _patch_client(monkeypatch, *responses: httpx.Response) -> _FakeClient:
    fake = _FakeClient(*responses)
    monkeypatch.setattr(censys_client, "get_client", lambda: fake)
    return fake


def _envelope(resource: dict) -> dict:
    return {"result": {"resource": resource, "extensions": {}}}


_CERT = {
    "fingerprint_sha256": "ab" * 32,
    "names": ["one.one.one.one"],
    "parsed": {"subject_dn": "CN=cloudflare-dns.com", "issuer_dn": "CN=DigiCert"},
}

_HOST = {
    "ip": "1.1.1.1",
    "service_count": 2,
    "services": [
        {
            "port": 443,
            "protocol": "HTTP",
            "transport_protocol": "tcp",
            "banner": "x" * 5000,
            "scan_time": "2026-10-20T00:00:00Z",
            "cert": _CERT,
        },
        {
            "port": 53,
            "protocol": "DNS",
            "transport_protocol": "udp",
            "scan_time": "2026-10-19T00:00:00Z",
        },
    ],
    "dns": {"names": ["one.one.one.one"]},
    "location": {"country": "Australia", "country_code": "AU", "city": "Brisbane"},
    "autonomous_system": {"asn": 13335, "name": "CLOUDFLARENET", "bgp_prefix": "1.1.1.0/24"},
}

_WEBPROPERTY = {
    "hostname": "example.com",
    "port": 443,
    "scan_time": "2026-10-20T00:00:00Z",
    "software": [
        {"vendor": "cloudflare", "product": "cloudflare", "version": None},
        {"vendor": "nginx", "product": "nginx", "version": "1.25"},
        {"cpe": "cpe:2.3:*"},
    ],
    "cert": _CERT,
}


def test_requires_a_token():
    with pytest.raises(ServiceAuthError):
        _run(censys_client.check_censys("1.1.1.1", "host", ""))


def test_host_lookup_sends_the_pat_and_trims_the_resource(monkeypatch):
    fake = _patch_client(monkeypatch, _response(200, json=_envelope(_HOST)))

    result = _run(censys_client.check_censys("1.1.1.1", "host", "pat"))

    assert fake.calls[0]["url"] == "https://api.platform.censys.io/v3/global/asset/host/1.1.1.1"
    assert fake.calls[0]["headers"]["Authorization"] == "Bearer pat"
    assert "params" not in fake.calls[0]  # no organization_id: the free wallet
    assert result["kind"] == "host"
    assert result["not_found"] is False
    assert [s["port"] for s in result["services"]] == [53, 443]
    assert "banner" not in result["services"][1]
    assert result["services"][1]["cert"]["subject_dn"] == "CN=cloudflare-dns.com"
    assert result["hostnames"] == ["one.one.one.one"]
    assert result["autonomous_system"]["asn"] == 13335


def test_domain_hits_the_443_web_property_first(monkeypatch):
    fake = _patch_client(monkeypatch, _response(200, json=_envelope(_WEBPROPERTY)))

    result = _run(censys_client.check_censys("example.com", "webproperty", "pat"))

    assert len(fake.calls) == 1
    assert fake.calls[0]["url"].endswith("/webproperty/example.com:443")
    assert result["kind"] == "webproperty"
    assert result["port"] == 443
    assert [s["product"] for s in result["software"]] == ["cloudflare", "nginx"]
    assert result["cert"]["fingerprint_sha256"] == "ab" * 32


def test_domain_falls_back_to_port_80_on_a_443_miss(monkeypatch):
    fake = _patch_client(
        monkeypatch,
        _response(404),
        _response(200, json=_envelope({**_WEBPROPERTY, "port": 80, "cert": None})),
    )

    result = _run(censys_client.check_censys("example.com", "webproperty", "pat"))

    assert [c["url"].rsplit(":", 1)[1] for c in fake.calls] == ["443", "80"]
    assert result["port"] == 80
    assert result["cert"] is None


def test_domain_missing_on_both_ports_is_not_found(monkeypatch):
    _patch_client(monkeypatch, _response(404), _response(404))

    result = _run(censys_client.check_censys("example.com", "webproperty", "pat"))

    assert result == {
        "kind": "webproperty",
        "reserved": False,
        "not_found": True,
        "hostname": "example.com",
        "software": [],
    }


def test_unknown_host_is_not_found(monkeypatch):
    fake = _patch_client(monkeypatch, _response(404))

    result = _run(censys_client.check_censys("8.8.4.4", "host", "pat"))

    assert len(fake.calls) == 1
    assert result["reserved"] is False

    assert result["not_found"] is True
    assert result["services"] == []


def test_401_says_to_regenerate_the_token(monkeypatch):
    _patch_client(monkeypatch, _response(401, json={"error": {"code": 401}}))

    with pytest.raises(ServiceAuthError, match="new one under API Access"):
        _run(censys_client.check_censys("1.1.1.1", "host", "pat"))


def test_403_about_organizations_says_it_needs_a_paid_org(monkeypatch):
    _patch_client(monkeypatch, _response(403, text='{"message": "organization required"}'))

    with pytest.raises(ServiceError, match="paid organization") as caught:
        _run(censys_client.check_censys("1.1.1.1", "host", "pat"))

    assert caught.value.status_code == 403


def test_a_body_without_result_resource_is_drift(monkeypatch):
    _patch_client(monkeypatch, _response(200, json={"result": {"extensions": {}}}))

    with pytest.raises(SourceDriftError):
        _run(censys_client.check_censys("1.1.1.1", "host", "pat"))


def test_a_reserved_ip_is_never_sent_to_censys(monkeypatch):
    fake = _patch_client(monkeypatch)

    result = _run(censys_client.check_censys("10.0.0.5", "host", "pat"))

    assert fake.calls == []
    assert result["reserved"] is True
    assert result["services"] == []


def test_a_host_without_services_is_an_empty_list_not_drift(monkeypatch):
    _patch_client(monkeypatch, _response(200, json=_envelope({"ip": "8.8.4.4"})))

    result = _run(censys_client.check_censys("8.8.4.4", "host", "pat"))

    assert result["services"] == []
    assert result["service_count"] == 0


@pytest.mark.parametrize(
    "resource",
    [
        {k: v for k, v in _HOST.items() if k != "services"},  # count says 2, list gone
        {**_HOST, "services": {"443": {}}},  # list became an object
        {k: v for k, v in _HOST.items() if k != "ip"},  # host lost its identity field
        {**_HOST, "location": "Australia"},
    ],
)
def test_a_renamed_or_retyped_host_field_is_drift(monkeypatch, resource):
    _patch_client(monkeypatch, _response(200, json=_envelope(resource)))

    with pytest.raises(SourceDriftError):
        _run(censys_client.check_censys("1.1.1.1", "host", "pat"))


@pytest.mark.parametrize(
    "resource",
    [
        {**_WEBPROPERTY, "software": "nginx"},
        {k: v for k, v in _WEBPROPERTY.items() if k != "hostname"},
    ],
)
def test_a_renamed_or_retyped_webproperty_field_is_drift(monkeypatch, resource):
    _patch_client(monkeypatch, _response(200, json=_envelope(resource)))

    with pytest.raises(SourceDriftError):
        _run(censys_client.check_censys("example.com", "webproperty", "pat"))


def test_software_keeps_censys_type_tags(monkeypatch):
    waf = {"vendor": "cloudflare", "product": "waf", "type": ["WAF"]}
    _patch_client(monkeypatch, _response(200, json=_envelope({**_WEBPROPERTY, "software": [waf]})))

    result = _run(censys_client.check_censys("example.com", "webproperty", "pat"))

    assert result["software"] == [
        {"vendor": "cloudflare", "product": "waf", "version": None, "types": ["WAF"]}
    ]
