import asyncio

import httpx
import pytest

from app.features.dork_runner.service.engines import base as engines_base
from app.features.dork_runner.service.engines.duckduckgo_engine import _resolve_result_url, search

_RESULT_HTML = """
<html><body>
<div class="result">
  <a class="result__a" href="https://duckduckgo.com/l/?uddg=https%3A%2F%2Fexample.com%2Fpage1&amp;rut=x">
    Example Page 1
  </a>
  <div class="result__snippet">First snippet</div>
</div>
<div class="result">
  <a class="result__a" href="https://example.com/page2">Example Page 2</a>
  <div class="result__snippet">Second snippet</div>
</div>
</body></html>
"""


def _run(coro):
    return asyncio.run(coro)


@pytest.fixture(autouse=True)
def _no_real_retry_delay(monkeypatch):
    async def _instant_sleep(_seconds):
        return None

    monkeypatch.setattr(engines_base.asyncio, "sleep", _instant_sleep)


class TestResolveResultUrl:
    def test_unwraps_a_duckduckgo_redirect_link(self):
        href = "//duckduckgo.com/l/?uddg=https%3A%2F%2Fexample.com%2Fpage&rut=abc"
        assert _resolve_result_url(href) == "https://example.com/page"

    def test_leaves_a_direct_link_untouched(self):
        assert _resolve_result_url("https://example.com/direct") == "https://example.com/direct"

    def test_empty_href_returns_empty_string(self):
        assert _resolve_result_url("") == ""


class TestSearch:
    def test_parses_titles_urls_and_snippets_from_result_blocks(self, patch_httpx_transport):
        patch_httpx_transport(lambda request: httpx.Response(200, text=_RESULT_HTML))

        results = _run(search("site:example.com"))

        assert len(results) == 2
        assert results[0].title == "Example Page 1"
        assert results[0].url == "https://example.com/page1"
        assert results[0].snippet == "First snippet"
        assert results[1].url == "https://example.com/page2"

    def test_sends_the_query_as_a_post_form_field(self, patch_httpx_transport):
        captured = {}

        def handler(request):
            captured["body"] = request.content
            return httpx.Response(200, text="<html></html>")

        patch_httpx_transport(handler)

        _run(search("site:example.com filetype:pdf"))

        assert b"site%3Aexample.com" in captured["body"]

    def test_returns_an_empty_list_when_the_fetch_fails(self, patch_httpx_transport):
        patch_httpx_transport(lambda request: httpx.Response(503, text="blocked"))

        results = _run(search("site:example.com"))

        assert results == []

    def test_returns_an_empty_list_when_no_result_blocks_are_present(self, patch_httpx_transport):
        patch_httpx_transport(
            lambda request: httpx.Response(200, text="<html><body>no results</body></html>")
        )

        results = _run(search("a-query-with-no-hits"))

        assert results == []
