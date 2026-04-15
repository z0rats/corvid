import logging
from datetime import datetime, timedelta, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from app.features.newsfeed.crud.news_articles_crud import (
    get_articles_after_cutoff,
    get_paginated_articles,
    get_recent_news_articles,
    get_news_article_by_id,
    get_news_articles_by_ids,
    update_news_article,
)
from app.features.newsfeed.crud.newsfeed_config_crud import get_newsfeed_config
from app.features.newsfeed.schemas.newsfeed_schemas import (
    ArticleIocsResponse, NewsArticleSchema, PaginatedArticlesResponse, RecentArticleSchema,
)

logger = logging.getLogger(__name__)


async def get_news_from_db(db: AsyncSession, limit: int = 500) -> list[NewsArticleSchema]:
    """Retrieve news articles within the configured retention period, newest first"""
    config = await get_newsfeed_config(db)

    if config.retention_days == 0:
        cutoff_date = datetime.min.replace(tzinfo=timezone.utc)
    else:
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=config.retention_days)

    articles = await get_articles_after_cutoff(db, cutoff_date, limit)
    logger.info("Retrieved %s news articles from database", len(articles))
    return [NewsArticleSchema.model_validate(article) for article in articles]


async def fetch_paginated_articles(
    db: AsyncSession,
    page: int = 1,
    page_size: int = 10,
    start_date: datetime | None = None,
    end_date: datetime | None = None,
    has_matches: bool | None = None,
    has_iocs: bool | None = None,
    has_relevant_iocs: bool | None = None,
    has_analysis: bool | None = None,
    has_note: bool | None = None,
    tlp: str | None = None,
    read: bool | None = None,
) -> PaginatedArticlesResponse:
    """Fetch paginated articles with boolean presence filters translated to null checks"""
    result = await get_paginated_articles(
        db=db,
        page=page,
        page_size=page_size,
        start_date=start_date,
        end_date=end_date,
        matches_null=None if has_matches is None else not has_matches,
        iocs_null=None if has_iocs is None else not has_iocs,
        relevant_iocs_null=None if has_relevant_iocs is None else not has_relevant_iocs,
        analysis_result_null=None if has_analysis is None else not has_analysis,
        note_null=None if has_note is None else not has_note,
        tlp=tlp,
        read=read,
    )
    return PaginatedArticlesResponse(**result)


async def get_article(db: AsyncSession, article_id: int) -> NewsArticleSchema | None:
    """Retrieve a single article by ID, returning None if not found"""
    article = await get_news_article_by_id(db, article_id)
    if not article:
        return None
    return NewsArticleSchema.model_validate(article)


async def get_articles_bulk(db: AsyncSession, article_ids: list[int]) -> list[NewsArticleSchema]:
    """Retrieve multiple articles by their IDs"""
    articles = await get_news_articles_by_ids(db, article_ids)
    missing_ids = set(article_ids) - {article.id for article in articles}
    if missing_ids:
        logger.warning("Some articles were not found: %s", missing_ids)
    return [NewsArticleSchema.model_validate(a) for a in articles]


async def update_article_details(
    db: AsyncSession,
    article_id: int,
    note: str | None = None,
    tlp: str | None = None,
    read: bool | None = None,
) -> NewsArticleSchema | None:
    """Update article note, TLP classification, or read status"""
    article = await update_news_article(db, article_id, note=note, tlp=tlp, read=read)
    if not article:
        return None
    logger.info("Updated article %s", article_id)
    return NewsArticleSchema.model_validate(article)


async def get_recent_articles(db: AsyncSession, time_filter: str = "7d") -> list[RecentArticleSchema]:
    """Retrieve recent articles filtered by a relative time range"""
    return await get_recent_news_articles(db, time_filter)


async def get_article_iocs(db: AsyncSession, article_id: int) -> ArticleIocsResponse | None:
    """Extract IOCs for a specific article, returning None if not found"""
    article = await get_news_article_by_id(db, article_id)
    if not article:
        return None
    iocs = article.iocs or {}
    return ArticleIocsResponse(**{key: iocs.get(key, []) for key in ArticleIocsResponse.model_fields})
