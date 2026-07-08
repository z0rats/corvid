import asyncio
import logging
import warnings

import feedparser
import httpx
from newspaper import Article

from app.core.config.settings import settings
from app.core.security.ssrf_guard import safe_get, SSRFValidationError
from app.features.ioc_tools.ioc_extractor.service.ioc_extractor_service import extract_iocs

logger = logging.getLogger(__name__)


async def _fetch_safely(url: str, timeout: float) -> bytes | None:
    """SSRF-safe GET: `url` comes from a feed source or a feed's own entries, both
    user-supplied, so it must be resolved/pinned to a public IP - see ssrf_guard.

    Fetching here (instead of letting newspaper/feedparser make their own request)
    is what lets us route the request through the guard at all.
    """
    try:
        async with httpx.AsyncClient(timeout=timeout, follow_redirects=False) as client:
            response = await safe_get(
                client, url, allow_private=settings.security.allow_private_network_targets
            )
            response.raise_for_status()
            return response.content
    except (SSRFValidationError, httpx.HTTPError) as e:
        logger.warning("Blocked or failed fetch for %s: %s", url, e)
        return None


def _parse_article(url: str, html: bytes) -> str:
    article = Article(url, language='en')
    article.download(input_html=html.decode('utf-8', errors='replace'))
    article.parse()
    return article.text


async def fetch_article_full_text(url: str, timeout: int = 30) -> str:
    """Fetches the full text of a news article using newspaper."""
    try:
        html = await _fetch_safely(url, timeout)
        if html is None:
            return ""
        return await asyncio.to_thread(_parse_article, url, html)
    except Exception as e:
        logger.error("Error fetching article from %s: %s", url, e)
        return ""


def _parse_feed_bytes(feed_url: str, raw: bytes) -> feedparser.FeedParserDict:
    with warnings.catch_warnings():
        warnings.filterwarnings("ignore", message=".*document declared as.*")
        warnings.filterwarnings("ignore", message=".*encoding.*")
        feed = feedparser.parse(raw)

    if feed.get('bozo', 0) == 1:
        exception = feed.get('bozo_exception')
        if exception:
            error_msg = str(exception)
            if "encoding" in error_msg.lower() or "declared as" in error_msg.lower():
                logger.debug("Feed encoding warning for %s: %s", feed_url, error_msg)
            else:
                logger.warning("Feed parsing warning for %s: %s", feed_url, error_msg)

    return feed


async def parse_feed(feed_url: str, timeout: int = 30) -> feedparser.FeedParserDict | None:
    """Parse a feed URL and return its entries."""
    try:
        raw = await _fetch_safely(feed_url, timeout)
        if raw is None:
            return None
        return await asyncio.to_thread(_parse_feed_bytes, feed_url, raw)
    except Exception as e:
        logger.error("Error parsing feed %s: %s", feed_url, e)
        return None


def extract_and_categorize_iocs(summary_content: str, full_text: str) -> dict[str, list[str]]:
    """Extracts and categorizes IOCs from article content."""
    try:
        summary_iocs = extract_iocs(summary_content)
        logger.info("Summary IOCs found: %s total IOCs", summary_iocs.statistics.total_unique_iocs)

        full_text_iocs = None
        if full_text:
            full_text_iocs = extract_iocs(full_text)
            logger.info("Full text IOCs found: %s total IOCs", full_text_iocs.statistics.total_unique_iocs)

        iocs_dict: dict[str, list] = {
            'ips': [],
            'md5': [],
            'sha1': [],
            'sha256': [],
            'emails': [],
            'cves': [],
        }

        all_ips = set(summary_iocs.ips)
        if full_text_iocs:
            all_ips.update(full_text_iocs.ips)
        iocs_dict['ips'] = list(all_ips)

        for ioc_type in ['md5', 'sha1', 'sha256', 'emails', 'cves']:
            combined = set(getattr(summary_iocs, ioc_type, []))
            if full_text_iocs:
                combined.update(getattr(full_text_iocs, ioc_type, []))
            iocs_dict[ioc_type] = list(combined)

        iocs_dict = {k: v for k, v in iocs_dict.items() if v}
        logger.info("Final combined IOCs: %s total", sum(len(v) for v in iocs_dict.values()))
        return iocs_dict

    except Exception as e:
        logger.error("Error extracting IOCs: %s", e)
        return {}
