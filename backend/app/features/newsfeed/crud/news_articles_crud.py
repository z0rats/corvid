import logging
from datetime import datetime, timedelta, timezone
from typing import Any

from sqlalchemy import Select, delete, func, or_, and_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.features.newsfeed.models.newsfeed_models import NewsArticle
from app.features.newsfeed.schemas.newsfeed_schemas import NewsArticleSchema, RecentArticleSchema
from app.features.newsfeed.utils.time_utils import parse_time_range

logger = logging.getLogger(__name__)


async def get_all_news_articles(db: AsyncSession, skip: int = 0, limit: int = 100) -> list[NewsArticle]:
    """Retrieve all news articles with pagination"""
    result = await db.execute(select(NewsArticle).offset(skip).limit(limit))
    return list(result.scalars().all())


async def get_news_articles_by_retention(db: AsyncSession, retention_days: int) -> list[NewsArticle]:
    """Retrieve news articles within the specified retention period"""
    cutoff_date = datetime.now(timezone.utc) - timedelta(days=retention_days)
    result = await db.execute(select(NewsArticle).where(NewsArticle.date >= cutoff_date))
    return list(result.scalars().all())


async def create_news_article(db: AsyncSession, news_article: NewsArticleSchema) -> NewsArticle | None:
    """Create a new news article, returning None if the link already exists.

    Uses flush (not commit) so the caller's session contract is respected.
    Rolls back only the failed flush on duplicates, leaving the session usable.
    """
    logger.debug("Creating news article: %s", news_article.title)
    db_news_article = NewsArticle(**news_article.model_dump(exclude={'id'}))
    db.add(db_news_article)
    try:
        await db.flush()
        logger.debug("Successfully created article: %s", news_article.title)
        return db_news_article
    except IntegrityError as e:
        await db.rollback()
        error_str = str(e.orig).lower() if e.orig else str(e).lower()
        if "unique" in error_str or "duplicate" in error_str:
            logger.debug("Article already exists (duplicate link): %s", news_article.link)
            return None
        logger.error("IntegrityError creating news article: %s", str(e))
        raise


async def get_articles_after_cutoff(
    db: AsyncSession, cutoff_date: datetime, limit: int = 500
) -> list[NewsArticle]:
    """Retrieve articles published on or after the cutoff date, ordered newest first"""
    result = await db.execute(
        select(NewsArticle)
        .where(NewsArticle.date >= cutoff_date)
        .order_by(NewsArticle.date.desc())
        .limit(limit)
    )
    return list(result.scalars().all())


async def update_news_article(
    db: AsyncSession,
    article_id: int,
    note: str | None = None,
    tlp: str | None = None,
    read: bool | None = None,
    analysis_result: str | None = None
) -> NewsArticle | None:
    """Update specific fields of a news article"""
    result = await db.execute(select(NewsArticle).where(NewsArticle.id == article_id))
    db_news_article = result.scalar_one_or_none()

    if not db_news_article:
        return None

    if note is not None:
        db_news_article.note = note
    if tlp is not None:
        logger.info("Updating TLP to: %s", tlp)
        db_news_article.tlp = tlp
    if read is not None:
        db_news_article.read = read
    if analysis_result is not None:
        db_news_article.analysis_result = analysis_result

    await db.flush()
    await db.refresh(db_news_article)
    return db_news_article


async def delete_old_news_articles(db: AsyncSession, retention_days: int) -> None:
    """Delete news articles older than the retention period. Skip when 0 (unlimited)"""
    if retention_days == 0:
        return
    cutoff_date = datetime.now(timezone.utc) - timedelta(days=retention_days)
    await db.execute(delete(NewsArticle).where(NewsArticle.date < cutoff_date))
    await db.flush()


async def check_article_exists(db: AsyncSession, link: str) -> bool:
    """Check if a news article with the given link already exists"""
    result = await db.execute(select(NewsArticle.id).where(NewsArticle.link == link))
    return result.first() is not None


async def get_news_article_by_id(db: AsyncSession, article_id: int) -> NewsArticle | None:
    """Retrieve a single news article by ID"""
    result = await db.execute(select(NewsArticle).where(NewsArticle.id == article_id))
    return result.scalar_one_or_none()


async def get_news_articles_by_ids(db: AsyncSession, article_ids: list[int]) -> list[NewsArticle]:
    """Retrieve multiple news articles by their IDs"""
    result = await db.execute(select(NewsArticle).where(NewsArticle.id.in_(article_ids)))
    return list(result.scalars().all())


async def get_recent_news_articles(db: AsyncSession, time_filter: str = "7d") -> list[RecentArticleSchema]:
    """Retrieve recent articles filtered by a relative time range"""
    try:
        cutoff_date = parse_time_range(time_filter)
    except ValueError:
        cutoff_date = None

    if cutoff_date is None:
        cutoff_date = datetime.min.replace(tzinfo=timezone.utc)

    result = await db.execute(
        select(NewsArticle.id, NewsArticle.title, NewsArticle.feedname, NewsArticle.date)
        .where(NewsArticle.date >= cutoff_date)
        .order_by(NewsArticle.date.desc())
    )

    return [
        RecentArticleSchema(id=row.id, title=row.title, feedname=row.feedname, date=row.date)
        for row in result
    ]


def _parse_date(value: str | datetime | None) -> datetime | None:
    """Parse a date value to datetime, accepting ISO strings or datetime objects"""
    if value is None:
        return None
    if isinstance(value, datetime):
        return value
    try:
        return datetime.fromisoformat(value)
    except ValueError:
        logger.warning("Invalid date filter value: %s", value)
        return None


def _filter_json_list(stmt: Select, column: Any, is_null: bool) -> Select:
    """Apply a presence filter on a JSON list column"""
    if is_null:
        return stmt.where(or_(column.is_(None), column == []))
    return stmt.where(and_(column.is_not(None), column != []))


def _filter_json_dict(stmt: Select, column: Any, is_null: bool) -> Select:
    """Apply a presence filter on a JSON dict column"""
    if is_null:
        return stmt.where(or_(column.is_(None), column == {}))
    return stmt.where(and_(column.is_not(None), column != {}))


def _filter_text(stmt: Select, column: Any, is_null: bool) -> Select:
    """Apply a presence filter on a plain text column"""
    if is_null:
        return stmt.where(or_(column.is_(None), column == ''))
    return stmt.where(and_(column.is_not(None), column != ''))


def apply_article_filters(
    stmt: Select,
    start_date: str | datetime | None = None,
    end_date: str | datetime | None = None,
    matches_null: bool | None = None,
    iocs_null: bool | None = None,
    relevant_iocs_null: bool | None = None,
    analysis_result_null: bool | None = None,
    note_null: bool | None = None,
    tlp: str | None = None,
    read: bool | None = None,
) -> Select:
    """Apply filters to a SQLAlchemy select statement"""
    parsed_start = _parse_date(start_date)
    parsed_end = _parse_date(end_date)

    if parsed_start:
        stmt = stmt.where(NewsArticle.date >= parsed_start)
    if parsed_end:
        stmt = stmt.where(NewsArticle.date <= parsed_end)

    if matches_null is not None:
        stmt = _filter_json_list(stmt, NewsArticle.matches, matches_null)
    if iocs_null is not None:
        stmt = _filter_json_dict(stmt, NewsArticle.iocs, iocs_null)
    if relevant_iocs_null is not None:
        stmt = _filter_json_list(stmt, NewsArticle.relevant_iocs, relevant_iocs_null)
    if analysis_result_null is not None:
        stmt = _filter_text(stmt, NewsArticle.analysis_result, analysis_result_null)
    if note_null is not None:
        stmt = _filter_text(stmt, NewsArticle.note, note_null)
    if tlp:
        stmt = stmt.where(NewsArticle.tlp == tlp)
    if read is not None:
        stmt = stmt.where(NewsArticle.read == read)

    return stmt


async def get_paginated_articles(
    db: AsyncSession,
    page: int = 1,
    page_size: int = 10,
    start_date: str | datetime | None = None,
    end_date: str | datetime | None = None,
    matches_null: bool | None = None,
    iocs_null: bool | None = None,
    relevant_iocs_null: bool | None = None,
    analysis_result_null: bool | None = None,
    note_null: bool | None = None,
    tlp: str | None = None,
    read: bool | None = None,
) -> dict[str, Any]:
    """Retrieve paginated news articles with optional filtering"""
    filter_args = dict(
        start_date=start_date, end_date=end_date,
        matches_null=matches_null, iocs_null=iocs_null,
        relevant_iocs_null=relevant_iocs_null,
        analysis_result_null=analysis_result_null,
        note_null=note_null, tlp=tlp, read=read,
    )

    total_count = (await db.execute(
        apply_article_filters(select(func.count(NewsArticle.id)), **filter_args)
    )).scalar_one()

    articles = (await db.execute(
        apply_article_filters(select(NewsArticle), **filter_args)
        .order_by(NewsArticle.date.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )).scalars().all()

    return {
        "total_count": total_count,
        "page": page,
        "page_size": page_size,
        "articles": [NewsArticleSchema.model_validate(article) for article in articles]
    }
