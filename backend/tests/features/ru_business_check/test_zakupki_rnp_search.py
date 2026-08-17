"""zakupki_rnp_service.fetch_rnp_entries network behavior, using httpx.MockTransport
(same pattern as test_fedresurs_search.py). Regression coverage for the real gate
confirmed live during development: any parameterized request needs both a session cookie
(minted by a plain GET against the search page) and a browser-shaped User-Agent, or the
site's WAF returns a bare 404 - never a helpful 403.
"""

import asyncio

import httpx
import pytest

from app.features.ru_business_check.service.zakupki_rnp_service import (
    ZakupkiRnpError,
    fetch_rnp_entries,
)

_RSS_TEMPLATE = """<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0"><channel><item>
<link>/epz/dishonestsupplier/view/info.html?reestrNumber=1&amp;law=FZ44</link>
<description>&lt;strong&gt;Реестровый номер: &lt;/strong&gt;1&lt;br/&gt;\
&lt;strong&gt;ИНН (аналог ИНН): &lt;/strong&gt;{inn}&lt;br/&gt;\
&lt;strong&gt;Статус записи: &lt;/strong&gt;Размещено&lt;br/&gt;</description>
</item></channel></rss>"""


def _run(coro):
    return asyncio.run(coro)


def _patch_transport(monkeypatch, handler):
    real_async_client = httpx.AsyncClient

    def factory(*args, **kwargs):
        kwargs["transport"] = httpx.MockTransport(handler)
        return real_async_client(*args, **kwargs)

    monkeypatch.setattr(httpx, "AsyncClient", factory)


class TestSessionAndRequestShape:
    def test_seeds_the_search_page_before_the_rss_request(self, monkeypatch):
        requested_paths = []

        def handler(request):
            requested_paths.append(request.url.path)
            if request.url.path.endswith("results.html"):
                return httpx.Response(
                    200, text="<html></html>", headers={"set-cookie": "session-cookie=abc"}
                )
            return httpx.Response(200, text=_RSS_TEMPLATE.format(inn="7712345678"))

        _patch_transport(monkeypatch, handler)

        _run(fetch_rnp_entries("7712345678"))

        assert requested_paths == [
            "/epz/dishonestsupplier/search/results.html",
            "/epz/dishonestsupplier/search/rss",
        ]

    def test_sends_a_browser_user_agent_and_the_seeded_cookie_on_the_rss_request(self, monkeypatch):
        captured = {}

        def handler(request):
            if request.url.path.endswith("results.html"):
                return httpx.Response(
                    200, text="<html></html>", headers={"set-cookie": "session-cookie=abc"}
                )
            captured["user_agent"] = request.headers.get("user-agent")
            captured["cookie"] = request.headers.get("cookie")
            return httpx.Response(200, text=_RSS_TEMPLATE.format(inn="7712345678"))

        _patch_transport(monkeypatch, handler)

        _run(fetch_rnp_entries("7712345678"))

        assert captured["user_agent"]
        assert "session-cookie=abc" in captured["cookie"]

    def test_sends_the_fixed_search_params_plus_the_inn(self, monkeypatch):
        captured = {}

        def handler(request):
            if request.url.path.endswith("results.html"):
                return httpx.Response(200, text="<html></html>")
            captured["params"] = dict(request.url.params)
            return httpx.Response(200, text=_RSS_TEMPLATE.format(inn="7712345678"))

        _patch_transport(monkeypatch, handler)

        _run(fetch_rnp_entries("7712345678"))

        assert captured["params"] == {
            "fz94": "on",
            "fz223": "on",
            "ppRf615": "on",
            "dsStatuses": "0",
            "sortBy": "UPDATE_DATE",
            "pageNumber": "1",
            "sortDirection": "false",
            "recordsPerPage": "_10",
            "searchString": "7712345678",
        }


class TestErrorHandling:
    def test_a_404_on_the_seed_request_raises_a_clean_error(self, monkeypatch):
        _patch_transport(monkeypatch, lambda request: httpx.Response(404, text="Not Found"))

        with pytest.raises(ZakupkiRnpError, match="HTTP 404"):
            _run(fetch_rnp_entries("7712345678"))

    def test_a_404_on_the_rss_request_raises_a_clean_error(self, monkeypatch):
        def handler(request):
            if request.url.path.endswith("results.html"):
                return httpx.Response(200, text="<html></html>")
            return httpx.Response(404, text="Not Found")

        _patch_transport(monkeypatch, handler)

        with pytest.raises(ZakupkiRnpError, match="HTTP 404"):
            _run(fetch_rnp_entries("7712345678"))

    def test_an_unrelated_server_error_raises_a_clean_error_not_the_raw_httpx_exception(
        self, monkeypatch
    ):
        _patch_transport(monkeypatch, lambda request: httpx.Response(500, text="error"))

        with pytest.raises(ZakupkiRnpError, match="HTTP 500"):
            _run(fetch_rnp_entries("7712345678"))


class TestSuccessPath:
    def test_returns_exact_matches_and_the_raw_payload(self, monkeypatch):
        def handler(request):
            if request.url.path.endswith("results.html"):
                return httpx.Response(200, text="<html></html>")
            return httpx.Response(200, text=_RSS_TEMPLATE.format(inn="7712345678"))

        _patch_transport(monkeypatch, handler)

        entries, raw = _run(fetch_rnp_entries("7712345678"))

        assert len(entries) == 1
        assert entries[0]["inn"] == "7712345678"
        assert "7712345678" in raw

    def test_no_matching_entries_is_a_clean_empty_list_not_an_error(self, monkeypatch):
        def handler(request):
            if request.url.path.endswith("results.html"):
                return httpx.Response(200, text="<html></html>")
            return httpx.Response(200, text="<rss><channel></channel></rss>")

        _patch_transport(monkeypatch, handler)

        entries, _ = _run(fetch_rnp_entries("7712345678"))

        assert entries == []

    def test_empty_inn_short_circuits_without_a_network_call(self, monkeypatch):
        def fail_handler(request):
            raise AssertionError("should not have made a request")

        _patch_transport(monkeypatch, fail_handler)

        entries, raw = _run(fetch_rnp_entries(""))

        assert entries == []
        assert raw == ""
