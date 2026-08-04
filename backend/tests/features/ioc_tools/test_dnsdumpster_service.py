import asyncio
from types import SimpleNamespace

import pytest

from app.core.exceptions import AppHTTPException
from app.features.ioc_tools.domain_finder.schemas.domain_schemas import DnsDumpsterRequest
from app.features.ioc_tools.domain_finder.service import dnsdumpster_service
from app.features.ioc_tools.domain_finder.service.dnsdumpster_service import perform_dnsdumpster_lookup

DNSDUMPSTER_SAMPLE = {
    "a": [
        {
            "host": "example.com",
            "ips": [
                {
                    "ip": "93.184.216.34",
                    "asn": "AS15133",
                    "asn_name": "EDGECAST",
                    "asn_range": "93.184.216.0/24",
                    "country": "United States",
                    "country_code": "US",
                    "ptr": "example-host.example.com",
                    "banners": {
                        "http": {"server": "nginx", "title": "Example Domain", "apps": ["nginx"]},
                        "https": {"server": "nginx", "cn": "example.com", "apps": []},
                    },
                }
            ],
        }
    ],
    "ns": [{"host": "a.iana-servers.net", "ips": []}],
    "mx": [],
    "cname": [],
    "txt": ["v=spf1 -all"],
    "total_a_recs": 1,
}


def _active_key(value="test-api-key"):
    return SimpleNamespace(key=value, is_active=True)


def test_perform_dnsdumpster_lookup_maps_response(monkeypatch):
    async def fake_get_apikey(db, name):
        return _active_key()

    async def fake_fetch(domain, api_key):
        assert api_key == "test-api-key"
        return DNSDUMPSTER_SAMPLE

    monkeypatch.setattr(dnsdumpster_service, "get_apikey", fake_get_apikey)
    monkeypatch.setattr(dnsdumpster_service, "fetch_dnsdumpster_data", fake_fetch)

    result = asyncio.run(perform_dnsdumpster_lookup(DnsDumpsterRequest(domain="example.com"), db=None))

    assert result.domain == "example.com"
    assert result.total_a_records == 1
    assert len(result.a) == 1
    assert result.a[0].host == "example.com"
    ip = result.a[0].ips[0]
    assert ip.ip == "93.184.216.34"
    assert ip.asn_name == "EDGECAST"
    assert ip.country_code == "US"
    assert ip.banner_http.server == "nginx"
    assert ip.banner_https.cn == "example.com"
    assert result.txt == ["v=spf1 -all"]


@pytest.mark.parametrize("apikey", [None, SimpleNamespace(key="", is_active=True), SimpleNamespace(key="abc", is_active=False)])
def test_perform_dnsdumpster_lookup_requires_configured_key(monkeypatch, apikey):
    async def fake_get_apikey(db, name):
        return apikey

    monkeypatch.setattr(dnsdumpster_service, "get_apikey", fake_get_apikey)

    with pytest.raises(AppHTTPException) as exc_info:
        asyncio.run(perform_dnsdumpster_lookup(DnsDumpsterRequest(domain="example.com"), db=None))

    assert exc_info.value.error_code == "DNSDUMPSTER_NOT_CONFIGURED"
    assert exc_info.value.status_code == 400


def test_perform_dnsdumpster_lookup_propagates_rate_limit(monkeypatch):
    async def fake_get_apikey(db, name):
        return _active_key()

    async def fake_fetch(domain, api_key):
        raise AppHTTPException(status_code=429, detail="rate limited", error_code="DNSDUMPSTER_RATE_LIMITED")

    monkeypatch.setattr(dnsdumpster_service, "get_apikey", fake_get_apikey)
    monkeypatch.setattr(dnsdumpster_service, "fetch_dnsdumpster_data", fake_fetch)

    with pytest.raises(AppHTTPException) as exc_info:
        asyncio.run(perform_dnsdumpster_lookup(DnsDumpsterRequest(domain="example.com"), db=None))

    assert exc_info.value.error_code == "DNSDUMPSTER_RATE_LIMITED"
    assert exc_info.value.status_code == 429
