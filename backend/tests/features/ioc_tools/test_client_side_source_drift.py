"""Clients that build their own result (CISA KEV, Library of Leaks, OpenPhish) can't use
`ProviderSpec.expects`, so each validates the raw source: a drifted payload raises
`SourceDriftError` (the engine turns it into "changed its response format"), a legitimately
empty answer stays "nothing found"."""

import httpx
import pytest

from app.core.external_sources.contract import SourceDriftError
from app.features.ioc_tools.ioc_lookup.single_lookup.service import external_api_clients
from tests.conftest import run as _run


def _response(*, json=None, text=None, status=200) -> httpx.Response:
    request = httpx.Request("GET", "https://source.example/x")
    if text is not None:
        return httpx.Response(status, request=request, text=text)
    return httpx.Response(status, request=request, json=json)


class _FakeClient:
    def __init__(self, response):
        self._response = response

    async def get(self, url, **kwargs):
        return self._response


@pytest.fixture
def serve(monkeypatch):
    def _serve(response):
        monkeypatch.setattr(external_api_clients, "get_client", lambda: _FakeClient(response))

    return _serve


@pytest.fixture(autouse=True)
def _cold_caches(monkeypatch):
    for cache in (external_api_clients._kev_cache, external_api_clients._openphish_cache):
        monkeypatch.setitem(cache, "fetched_at", 0.0)
    monkeypatch.setitem(external_api_clients._kev_cache, "catalog", None)
    monkeypatch.setitem(external_api_clients._openphish_cache, "urls", None)
    monkeypatch.setitem(external_api_clients._openphish_cache, "domains", None)


class TestCisaKev:
    def test_a_catalog_without_the_vulnerabilities_list_is_drift_not_not_listed(self, serve):
        serve(_response(json={"title": "KEV", "count": 0}))
        with pytest.raises(SourceDriftError, match="vulnerabilities"):
            _run(external_api_clients.check_cisa_kev("CVE-2021-44228"))

    def test_entries_without_a_cve_id_are_drift(self, serve):
        serve(_response(json={"vulnerabilities": [{"cve": "CVE-2021-44228"}]}))
        with pytest.raises(SourceDriftError, match="cveID"):
            _run(external_api_clients.check_cisa_kev("CVE-2021-44228"))

    def test_a_cve_missing_from_a_well_formed_catalog_is_not_listed(self, serve):
        serve(_response(json={"vulnerabilities": [{"cveID": "CVE-2020-0001"}]}))
        assert _run(external_api_clients.check_cisa_kev("CVE-2021-44228")) == {"listed": False}


class TestLibraryOfLeaks:
    def test_a_response_without_total_or_facets_is_drift_not_zero_hits(self, serve):
        serve(_response(json={"status": "ok", "results": []}))
        with pytest.raises(SourceDriftError, match="total"):
            _run(external_api_clients.check_libraryofleaks("example.com"))

    def test_zero_hits_is_an_empty_result(self, serve):
        serve(_response(json={"total": 0, "facets": {"collection_id": {"values": []}}}))
        result = _run(external_api_clients.check_libraryofleaks("example.com"))
        assert result["total_hits"] == 0
        assert result["collections"] == []


class TestOpenPhish:
    def test_a_feed_that_is_an_html_page_is_drift(self, serve):
        serve(_response(text="<html><body>Rate limited</body></html>"))
        with pytest.raises(SourceDriftError, match="no URL lines"):
            _run(external_api_clients.check_openphish("evil.example.com"))

    def test_an_empty_feed_is_drift(self, serve):
        serve(_response(text="\n"))
        with pytest.raises(SourceDriftError):
            _run(external_api_clients.check_openphish("evil.example.com"))

    def test_an_unlisted_url_in_a_well_formed_feed_is_not_listed(self, serve):
        serve(_response(text="http://evil.example.com/login\n"))
        result = _run(external_api_clients.check_openphish("https://clean.example.org/"))
        assert result == {"listed": False, "matched_urls": []}
