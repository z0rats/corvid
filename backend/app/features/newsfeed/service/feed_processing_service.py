import asyncio
import logging
import re
import time
from datetime import datetime, timezone
from typing import Any
from urllib.parse import urlparse

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import managed_session
from app.features.newsfeed.schemas.newsfeed_schemas import NewsArticleSchema
from app.features.newsfeed.crud.news_articles_crud import check_article_exists, create_news_article
from app.features.newsfeed.crud.newsfeed_settings_crud import record_feed_fetch_result
from app.features.newsfeed.utils.fetching import parse_feed, fetch_article_full_text, extract_and_categorize_iocs
from app.core.settings.keywords.crud.keywords_settings_crud import get_keywords

logger = logging.getLogger(__name__)

SKIP_PROCESSING_DOMAINS = {'bsky.app', 'reddit.com', 'www.reddit.com'}
MAX_CONCURRENT_REQUESTS = 10
CHUNK_SIZE = 20
HTML_TAG_PATTERN = re.compile(r'<[^>]+>')

_semaphore: asyncio.Semaphore | None = None


def _get_semaphore() -> asyncio.Semaphore:
    """Return the concurrency semaphore, creating it lazily within the running event loop."""
    global _semaphore
    if _semaphore is None:
        _semaphore = asyncio.Semaphore(MAX_CONCURRENT_REQUESTS)
    return _semaphore


def reset_semaphore() -> None:
    """Reset the concurrency semaphore (for testing only)."""
    global _semaphore
    _semaphore = None


async def check_article_exists_async(link: str) -> bool:
    """Check if article already exists in database using its own session"""
    try:
        async with managed_session() as db:
            return await check_article_exists(db, link)
    except Exception as e:
        logger.error("Error checking article existence: %s", e)
        return False


async def get_full_text_async(link: str) -> str:
    """Get full text of article asynchronously"""
    try:
        return await fetch_article_full_text(link)
    except Exception as e:
        logger.warning("Failed to fetch full text for %s: %s", link, e)
        return ""


async def extract_iocs_async(content: str, full_text: str) -> dict | None:
    """Extract IOCs from content asynchronously"""
    try:
        return await asyncio.to_thread(extract_and_categorize_iocs, content, full_text)
    except Exception as e:
        logger.warning("Failed to extract IOCs: %s", e)
        return None


async def gather_article_data(
    link: str,
    process_full_text: bool,
    title: str,
    summary: str
) -> tuple[str, dict | None]:
    """Gather article data concurrently"""
    if not process_full_text:
        combined_content = f"{title} {summary}"
        iocs_dict = await extract_iocs_async(combined_content, "")
        return "", iocs_dict

    full_text = await get_full_text_async(link)
    combined_content = f"{title} {summary} {full_text}" if full_text else f"{title} {summary}"
    iocs_dict = await extract_iocs_async(combined_content, full_text)

    return full_text, iocs_dict


def parse_published_date(post: Any) -> datetime:
    """Parse published date from a feedparser entry"""
    try:
        if hasattr(post, 'published_parsed') and post.published_parsed:
            return datetime.fromtimestamp(time.mktime(post.published_parsed), tz=timezone.utc)
    except Exception as e:
        logger.error("Error parsing published date: %s", e)
    return datetime.now(timezone.utc)


async def store_article_async(
    entry: dict[str, Any],
    post: dict[str, Any],
    full_text: str,
    iocs_dict: dict | None,
    keyword_matching_enabled: bool,
    keywords: list[str]
) -> None:
    """Store processed article in database using its own session"""
    try:
        title = post.get('title', '')
        summary = post.get('summary', post.get('description', ''))
        all_content = f"{title} {summary} {full_text}" if full_text else f"{title} {summary}"

        matches = None
        if keyword_matching_enabled:
            matches = [k for k in keywords if k.lower() in all_content.lower()]

        news_article = NewsArticleSchema(
            feedname=entry['name'],
            icon=entry['icon'],
            title=title,
            summary=HTML_TAG_PATTERN.sub('', summary),
            full_text=full_text if full_text else None,
            date=parse_published_date(post),
            link=post.get('link', ''),
            fetched_at=datetime.now(timezone.utc),
            matches=matches if matches else None,
            iocs=iocs_dict,
            relevant_iocs=None,
            analysis_result=None,
            note=None,
            tlp="TLP:CLEAR",
            read=False
        )

        async with managed_session() as db:
            result = await create_news_article(db, news_article)

        if result is not None:
            logger.info("Stored article: %s", title)
        else:
            logger.debug("Article already exists, skipped: %s", title)

    except Exception as e:
        logger.error("Error storing article %s: %s", post.get('title', 'Unknown'), e)


async def process_feed_entry(
    entry: dict[str, Any],
    post: dict[str, Any],
    keyword_matching_enabled: bool,
    keywords: list[str]
) -> None:
    """Process individual feed entry asynchronously with rate limiting"""
    try:
        async with _get_semaphore():
            link = post.get('link', '')
            if not link:
                logger.warning("No link found in feed entry, skipping")
                return

            if await check_article_exists_async(link):
                logger.debug("Article already exists: %s", post.get('title', 'No title'))
                return

            domain = urlparse(link).netloc.lower()
            process_full_text = domain not in SKIP_PROCESSING_DOMAINS

            full_text, iocs_dict = await gather_article_data(
                link,
                process_full_text,
                post.get('title', ''),
                post.get('summary', post.get('description', ''))
            )

            await store_article_async(
                entry, post, full_text, iocs_dict,
                keyword_matching_enabled, keywords
            )

    except Exception as e:
        logger.warning("Failed to process feed entry %s: %s", post.get('title', 'Unknown'), e)


async def record_feed_status(feed_name: str, success: bool, error: str | None = None) -> None:
    """Persist the outcome of a fetch attempt for a feed using its own session"""
    try:
        async with managed_session() as db:
            await record_feed_fetch_result(db, feed_name, success, error)
    except Exception as e:
        logger.error("Failed to record fetch status for feed %s: %s", feed_name, e)


async def process_feed_chunk(
    feeds: list[dict[str, Any]],
    keyword_matching_enabled: bool,
    keywords: list[str]
) -> None:
    """Process a chunk of feeds concurrently"""
    tasks = []

    for entry in feeds:
        try:
            feed = await parse_feed(entry['url'])
            if not feed or not feed.entries:
                logger.warning("No entries found in feed: %s", entry['name'])
                await record_feed_status(entry['name'], success=False, error="Feed unreachable or returned no entries")
                continue

            await record_feed_status(entry['name'], success=True)
            tasks.extend([
                process_feed_entry(entry, post, keyword_matching_enabled, keywords)
                for post in feed.entries
            ])
        except Exception as e:
            logger.error("Error processing feed %s: %s", entry['name'], e)
            await record_feed_status(entry['name'], success=False, error=str(e))

    if tasks:
        await asyncio.gather(*tasks)


async def fetch_and_store_news(db: AsyncSession) -> None:
    """Fetch and store news articles from configured feeds asynchronously.

    The caller-provided session is used only for reading configuration.
    Each article write gets its own session via managed_session() to
    avoid sharing a session across concurrent tasks.
    """
    from app.features.newsfeed.crud.newsfeed_config_crud import get_newsfeed_config, update_last_fetch_timestamp
    from app.features.newsfeed.crud.newsfeed_settings_crud import get_all_newsfeed_settings

    logger.info("Starting fetch_and_store_news")
    try:
        config = await get_newsfeed_config(db)
        keyword_matching_enabled = config.keyword_matching_enabled
        keywords = [k.keyword for k in await get_keywords(db)] if keyword_matching_enabled else []

        feeds = [
            {"name": feed.name, "url": str(feed.url), "icon": feed.icon}
            for feed in await get_all_newsfeed_settings(db) if feed.enabled
        ]

        for i in range(0, len(feeds), CHUNK_SIZE):
            chunk = feeds[i:i + CHUNK_SIZE]
            await process_feed_chunk(chunk, keyword_matching_enabled, keywords)

        await update_last_fetch_timestamp(db)
        logger.info("Completed fetch_and_store_news")

    except Exception as e:
        logger.error("Error in fetch_and_store_news: %s", e)
        await db.rollback()
        raise
