import asyncio

import httpx
import pytest

from app.features.dork_runner.service.engines import base as engines_base
from app.features.dork_runner.service.engines.google_engine import search

_RESULT_HTML = """
<html><body>
<div class="g">
  <a href="https://example.com/page1"><h3>Example Page 1</h3></a>
  <div class="VwiC3b">First snippet</div>
</div>
<div class="g">
  <a href="/local-link-not-http"><h3>Should be skipped</h3></a>
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


class TestSearch:
    def test_parses_result_blocks_and_skips_non_http_links(self, patch_httpx_transport):
        patch_httpx_transport(lambda request: httpx.Response(200, text=_RESULT_HTML))

        results = _run(search("site:example.com"))

        assert len(results) == 1
        assert results[0].title == "Example Page 1"
        assert results[0].url == "https://example.com/page1"
        assert results[0].snippet == "First snippet"

    def test_returns_an_empty_list_when_blocked(self, patch_httpx_transport):
        patch_httpx_transport(lambda request: httpx.Response(429, text="CAPTCHA"))

        assert _run(search("site:example.com")) == []
