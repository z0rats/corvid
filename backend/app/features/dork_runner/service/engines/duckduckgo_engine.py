"""DuckDuckGo HTML endpoint - the default/recommended dork engine.

https://html.duckduckgo.com/html/ requires no JS and no API key, and is far
less aggressive about blocking scripted queries than Google/Bing.
"""
import logging
from urllib.parse import parse_qs, urlparse

from bs4 import BeautifulSoup

from app.features.dork_runner.config.search_engines_config import DUCKDUCKGO_URL, MAX_RESULTS_PER_QUERY
from .base import RawResult, fetch_html

logger = logging.getLogger(__name__)


def _resolve_result_url(href: str) -> str:
    """DuckDuckGo's HTML result links are redirects through duckduckgo.com/l/?uddg=<target>."""
    if not href:
        return ""
    if href.startswith("//"):
        href = f"https:{href}"
    parsed = urlparse(href)
    hostname = parsed.hostname or ""
    is_duckduckgo = hostname == "duckduckgo.com" or hostname.endswith(".duckduckgo.com")
    if is_duckduckgo and parsed.path.startswith("/l/"):
        target = parse_qs(parsed.query).get("uddg")
        if target:
            return target[0]
    return href


async def search(query: str) -> list[RawResult]:
    html = await fetch_html("POST", DUCKDUCKGO_URL, data={"q": query})
    if not html:
        return []

    soup = BeautifulSoup(html, "html.parser")
    results: list[RawResult] = []

    for block in soup.select("div.result"):
        title_tag = block.select_one("a.result__a")
        if not title_tag:
            continue
        title = title_tag.get_text(strip=True)
        url = _resolve_result_url(title_tag.get("href", ""))
        if not url:
            continue
        snippet_tag = block.select_one(".result__snippet")
        snippet = snippet_tag.get_text(strip=True) if snippet_tag else ""
        results.append(RawResult(title=title, url=url, snippet=snippet))
        if len(results) >= MAX_RESULTS_PER_QUERY:
            break

    if not results:
        logger.debug("DuckDuckGo returned no parseable results for query: %s", query)

    return results
