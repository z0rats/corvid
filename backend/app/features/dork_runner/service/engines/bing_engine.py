"""Bing web scraping - best-effort only (see google_engine.py's docstring; same caveats apply)."""
import logging

from bs4 import BeautifulSoup

from app.features.dork_runner.config.search_engines_config import BING_URL, MAX_RESULTS_PER_QUERY
from .base import RawResult, fetch_html

logger = logging.getLogger(__name__)


async def search(query: str) -> list[RawResult]:
    html = await fetch_html("GET", BING_URL, params={"q": query, "count": MAX_RESULTS_PER_QUERY})
    if not html:
        return []

    soup = BeautifulSoup(html, "html.parser")
    results: list[RawResult] = []

    for block in soup.select("li.b_algo"):
        link_tag = block.select_one("h2 a[href]")
        if not link_tag:
            continue
        url = link_tag.get("href", "")
        if not url.startswith("http"):
            continue
        title = link_tag.get_text(strip=True)
        snippet_tag = block.select_one(".b_caption p")
        snippet = snippet_tag.get_text(strip=True) if snippet_tag else ""
        results.append(RawResult(title=title, url=url, snippet=snippet))
        if len(results) >= MAX_RESULTS_PER_QUERY:
            break

    if not results:
        logger.debug("Bing returned no parseable results for query (likely blocked/CAPTCHA'd): %s", query)

    return results
