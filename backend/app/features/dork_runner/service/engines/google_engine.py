"""Google web scraping - best-effort only.

Google actively blocks/CAPTCHAs scripted queries, often after a single request
with no session cookies. Parsing here is intentionally defensive: a change in
Google's markup or a block page just yields zero results rather than an error,
since that's expected, not exceptional, behavior for this engine.
"""
import logging

from bs4 import BeautifulSoup

from app.features.dork_runner.config.search_engines_config import GOOGLE_URL, MAX_RESULTS_PER_QUERY
from .base import RawResult, fetch_html

logger = logging.getLogger(__name__)


async def search(query: str) -> list[RawResult]:
    html = await fetch_html("GET", GOOGLE_URL, params={"q": query, "num": MAX_RESULTS_PER_QUERY, "hl": "en"})
    if not html:
        return []

    soup = BeautifulSoup(html, "html.parser")
    results: list[RawResult] = []

    for block in soup.select("div.g"):
        link_tag = block.select_one("a[href]")
        heading_tag = block.select_one("h3")
        if not link_tag or not heading_tag:
            continue
        url = link_tag.get("href", "")
        if not url.startswith("http"):
            continue
        title = heading_tag.get_text(strip=True)
        snippet_tag = block.select_one("div[data-sncf], div.VwiC3b, span.aCOpRe")
        snippet = snippet_tag.get_text(strip=True) if snippet_tag else ""
        results.append(RawResult(title=title, url=url, snippet=snippet))
        if len(results) >= MAX_RESULTS_PER_QUERY:
            break

    if not results:
        logger.debug("Google returned no parseable results for query (likely blocked/CAPTCHA'd): %s", query)

    return results
