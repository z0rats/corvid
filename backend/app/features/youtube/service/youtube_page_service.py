"""Best-effort scrape of a YouTube video page's <meta>/<link> tags (schema.org
VideoObject itemprops + Open Graph) for fields oEmbed doesn't expose: description,
duration, publish date, view count, tags/keywords, channel ID. Fixed host
(www.youtube.com); only the already-validated video ID is user-derived.

YouTube doesn't publish this as a stable API - it's the same public HTML any
browser gets, so an upstream markup change can silently drop fields here. Every
extracted field is optional and failures return an empty dict rather than
raising, since fetch_oembed_data already covers the guaranteed baseline.
"""

import logging

import httpx
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

VIDEO_PAGE_TIMEOUT = 10.0
DEFAULT_HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; Corvid-YouTube-Lookup/1.0)",
    "Accept-Language": "en-US,en;q=0.9",
}


async def fetch_page_metadata(video_url: str) -> dict[str, str]:
    """Fetch and parse a YouTube video page's meta/link/itemprop tags.

    Returns an empty dict on any failure - this is enrichment on top of oEmbed,
    not a required data source.
    """
    try:
        async with httpx.AsyncClient(timeout=VIDEO_PAGE_TIMEOUT, headers=DEFAULT_HEADERS) as client:
            response = await client.get(video_url)
            response.raise_for_status()
            return _parse_meta_tags(response.text)
    except Exception as e:
        logger.warning("Failed to scrape YouTube page metadata for %s: %s", video_url, e)
        return {}


def _parse_meta_tags(html: str) -> dict[str, str]:
    soup = BeautifulSoup(html, "lxml")
    fields: dict[str, str] = {}

    for meta in soup.find_all("meta", attrs={"itemprop": True}):
        name = meta.get("itemprop")
        content = meta.get("content")
        if name and content is not None:
            fields.setdefault(name, content)

    for link in soup.find_all("link", attrs={"itemprop": True}):
        name = link.get("itemprop")
        href = link.get("href")
        if name and href is not None:
            fields.setdefault(name, href)

    for meta in soup.find_all("meta", attrs={"property": True}):
        prop = meta.get("property")
        content = meta.get("content")
        if prop and prop.startswith("og:") and content is not None:
            fields.setdefault(prop, content)

    keywords = soup.find("meta", attrs={"name": "keywords"})
    if keywords and keywords.get("content"):
        fields.setdefault("keywords", keywords["content"])

    return fields
