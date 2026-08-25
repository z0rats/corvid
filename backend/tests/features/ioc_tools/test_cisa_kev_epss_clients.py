"""check_cisa_kev and search_first_epss: both keyless CVE-only providers.

check_cisa_kev is the odd one out among external_api_clients.py's provider functions - CISA
only publishes a full catalog dump (no per-CVE endpoint), so it fetches-and-caches the whole
list in-process on a TTL rather than making one request per lookup like every other provider.
search_first_epss is the plain keyless GET+params baseline (same shape as check_ffraud).
"""

import time

import httpx
import pytest

from app.features.ioc_tools.ioc_lookup.single_lookup.service import external_api_clients
from app.features.ioc_tools.ioc_lookup.single_lookup.service.client_base import ServiceError
from tests.conftest import run as _run


def _response(status_code: int, json=None) -> httpx.Response:
    request = httpx.Request("GET", "https://service.example/api")
    return httpx.Response(status_code, request=request, json=json if json is not None else {})


class _FakeClient:
    """Records every call made against it and returns a canned response."""

    def __init__(self, response: httpx.Response):
        self._response = response
        self.calls: list[dict] = []

    async def get(self, url, **kwargs):
        self.calls.append({"url": url, **kwargs})
        return self._response


def _patch_client(monkeypatch, response: httpx.Response) -> _FakeClient:
    fake = _FakeClient(response)
    monkeypatch.setattr(external_api_clients, "get_client", lambda: fake)
    return fake


@pytest.fixture(autouse=True)
def _reset_kev_cache(monkeypatch):
    """Every test starts from a cold KEV cache, so fetch behavior is deterministic."""
    monkeypatch.setitem(external_api_clients._kev_cache, "catalog", None)
    monkeypatch.setitem(external_api_clients._kev_cache, "fetched_at", 0.0)


_KEV_CATALOG_RESPONSE = {
    "catalogVersion": "2026.08.20",
    "vulnerabilities": [
        {
            "cveID": "CVE-2024-1234",
            "vendorProject": "Example Corp",
            "product": "Widget",
            "shortDescription": "Example RCE",
            "dateAdded": "2024-02-01",
            "dueDate": "2024-02-22",
            "knownRansomwareCampaignUse": "Known",
        }
    ],
}


class TestCheckCisaKev:
    def test_listed_cve_returns_catalog_entry(self, monkeypatch):
        _patch_client(monkeypatch, _response(200, json=_KEV_CATALOG_RESPONSE))

        result = _run(external_api_clients.check_cisa_kev("CVE-2024-1234"))

        assert result["listed"] is True
        assert result["knownRansomwareCampaignUse"] == "Known"

    def test_lookup_is_case_insensitive(self, monkeypatch):
        _patch_client(monkeypatch, _response(200, json=_KEV_CATALOG_RESPONSE))

        result = _run(external_api_clients.check_cisa_kev("cve-2024-1234"))

        assert result["listed"] is True

    def test_unlisted_cve_returns_not_listed(self, monkeypatch):
        _patch_client(monkeypatch, _response(200, json=_KEV_CATALOG_RESPONSE))

        result = _run(external_api_clients.check_cisa_kev("CVE-2099-9999"))

        assert result == {"listed": False}

    def test_second_lookup_reuses_cached_catalog(self, monkeypatch):
        fake = _patch_client(monkeypatch, _response(200, json=_KEV_CATALOG_RESPONSE))

        _run(external_api_clients.check_cisa_kev("CVE-2024-1234"))
        _run(external_api_clients.check_cisa_kev("CVE-2099-9999"))

        assert len(fake.calls) == 1

    def test_expired_cache_triggers_refetch(self, monkeypatch):
        fake = _patch_client(monkeypatch, _response(200, json=_KEV_CATALOG_RESPONSE))

        _run(external_api_clients.check_cisa_kev("CVE-2024-1234"))
        # 0.0 isn't reliably "in the past enough": time.monotonic()'s reference point is
        # arbitrary (often system boot), so on a freshly-booted CI runner it can still be
        # under the TTL - a relative offset is the only portable way to force expiry.
        monkeypatch.setitem(
            external_api_clients._kev_cache,
            "fetched_at",
            time.monotonic() - external_api_clients._KEV_CACHE_TTL_SECONDS - 1,
        )
        _run(external_api_clients.check_cisa_kev("CVE-2024-1234"))

        assert len(fake.calls) == 2

    def test_raises_service_error_on_http_error(self, monkeypatch):
        _patch_client(monkeypatch, _response(503, json={"message": "unavailable"}))

        with pytest.raises(ServiceError):
            _run(external_api_clients.check_cisa_kev("CVE-2024-1234"))


class TestSearchFirstEpss:
    def test_sends_cve_as_query_param(self, monkeypatch):
        fake = _patch_client(monkeypatch, _response(200, json={"data": []}))

        _run(external_api_clients.search_first_epss("CVE-2024-1234"))

        assert fake.calls[0]["url"] == "https://api.first.org/data/v1/epss"
        assert fake.calls[0]["params"] == {"cve": "CVE-2024-1234"}

    def test_returns_parsed_json_on_success(self, monkeypatch):
        payload = {"data": [{"cve": "CVE-2024-1234", "epss": "0.94", "percentile": "0.99"}]}
        _patch_client(monkeypatch, _response(200, json=payload))

        result = _run(external_api_clients.search_first_epss("CVE-2024-1234"))

        assert result == payload

    def test_raises_service_error_on_http_error(self, monkeypatch):
        _patch_client(monkeypatch, _response(500, json={"message": "internal error"}))

        with pytest.raises(ServiceError):
            _run(external_api_clients.search_first_epss("CVE-2024-1234"))
