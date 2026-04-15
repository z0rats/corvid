import logging
from datetime import datetime

from fastapi import APIRouter, BackgroundTasks, Query, status
from fastapi.responses import StreamingResponse

from app.core.database import managed_session
from app.core.dependencies import ReadSessionDep, SessionDep
from app.features.newsfeed.schemas.newsfeed_schemas import (
    ArticleAnalysisResponse,
    MessageResponse,
    NewsArticleSchema,
    PaginatedArticlesResponse,
    RecentArticleSchema,
)
from app.features.newsfeed.service.article_retrieval_service import (
    fetch_paginated_articles,
    get_news_from_db,
    get_recent_articles,
)
from app.features.newsfeed.service.feed_processing_service import fetch_and_store_news
from app.features.newsfeed.service.report_generator_service import (
    analyze_and_rank_top_articles,
    analyze_top_articles_stream,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/newsfeed", tags=["Newsfeed"])


@router.get(
    "",
    response_model=list[NewsArticleSchema],
    response_model_exclude_none=True,
    summary="List all articles",
    description="Retrieve news articles from the database. Use the paginated /articles endpoint for large datasets.",
    responses={500: {"description": "Internal server error"}},
)
async def get_news(
    db: ReadSessionDep,
    limit: int = Query(500, ge=1, le=1000, description="Maximum number of articles to return"),
) -> list[NewsArticleSchema]:
    """Get news articles from the database"""
    logger.info("Fetching news articles from database (limit=%s)", limit)
    return await get_news_from_db(db, limit=limit)


@router.get(
    "/articles",
    response_model=PaginatedArticlesResponse,
    response_model_exclude_none=True,
    summary="List articles (paginated)",
    description="Retrieve news articles with pagination and optional filters for date range, IOC presence, TLP, and read status",
)
async def get_paginated_articles_route(
    db: ReadSessionDep,
    page: int = Query(1, ge=1, description="Page number for pagination"),
    page_size: int = Query(10, ge=1, le=100, description="Number of articles per page"),
    start_date: datetime | None = Query(None, description="Start date (ISO format)"),
    end_date: datetime | None = Query(None, description="End date (ISO format)"),
    has_matches: bool | None = Query(None, description="Filter for articles with keyword matches"),
    has_iocs: bool | None = Query(None, description="Filter for articles with IOCs"),
    has_relevant_iocs: bool | None = Query(None, description="Filter for articles with relevant IOCs"),
    has_analysis: bool | None = Query(None, description="Filter for articles with analysis results"),
    has_note: bool | None = Query(None, description="Filter for articles with notes"),
    tlp: str | None = Query(None, description="Filter by TLP value"),
    read: bool | None = Query(None, description="Filter by read status"),
) -> PaginatedArticlesResponse:
    """Fetch paginated articles with optional filtering"""
    logger.info("Fetching paginated articles - Page: %s, Size: %s", page, page_size)
    return await fetch_paginated_articles(
        db, page, page_size, start_date, end_date,
        has_matches=has_matches, has_iocs=has_iocs, has_relevant_iocs=has_relevant_iocs,
        has_analysis=has_analysis, has_note=has_note, tlp=tlp, read=read
    )


@router.get(
    "/articles/recent",
    response_model=list[RecentArticleSchema],
    summary="List recent articles",
    description="Get a lightweight list of recent article summaries filtered by a relative time window",
)
async def get_recent_articles_route(
    db: ReadSessionDep,
    time_filter: str = Query("7d", pattern="^(8h|24h|2d|7d|30d|alltime)$"),
) -> list[RecentArticleSchema]:
    """Get recent articles based on time filter. Returns an empty list if no articles are found."""
    logger.info("Fetching recent articles with time filter: %s", time_filter)
    return await get_recent_articles(db, time_filter)


async def _run_news_fetch() -> None:
    """Execute news fetch with its own database session, independent of any request lifecycle."""
    async with managed_session() as db:
        await fetch_and_store_news(db)


@router.post(
    "/fetch",
    response_model=MessageResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Trigger news fetch (background)",
    description="Trigger a background job to fetch and store new articles from all enabled feeds",
)
async def fetch_news(background_tasks: BackgroundTasks) -> MessageResponse:
    """Trigger a background news fetch and store cycle"""
    logger.info("Initiating background news fetch")
    background_tasks.add_task(_run_news_fetch)
    return MessageResponse(message="News fetch initiated")


@router.post(
    "/fetch_and_get",
    response_model=MessageResponse,
    summary="Fetch news and wait for completion",
    description="Fetch and store new articles from all enabled feeds, waiting for the operation to complete before responding",
)
async def fetch_and_get_news() -> MessageResponse:
    """Fetch news synchronously so the caller knows when it's done"""
    logger.info("Starting synchronous news fetch")
    await _run_news_fetch()
    return MessageResponse(message="News fetch completed")


@router.post(
    "/analysis/top-articles",
    response_model=ArticleAnalysisResponse,
    summary="Analyze top articles",
    description="Analyze and rank the 10 most relevant recent cybersecurity articles using an LLM",
)
async def post_analyze_top_articles(db: SessionDep) -> ArticleAnalysisResponse:
    """Analyze and rank the top 10 most relevant recent cybersecurity articles"""
    logger.info("Starting analysis of top articles")
    results = await analyze_and_rank_top_articles(db)
    return ArticleAnalysisResponse(articles_analysis=results)


@router.get(
    "/analysis/top-articles/stream",
    summary="Stream top article analysis",
    description="Stream LLM analysis of the top 10 articles via Server-Sent Events. Yields ranking, analysis, and complete events.",
)
async def get_analyze_top_articles_stream() -> StreamingResponse:
    """Stream analysis of top 10 articles via Server-Sent Events.

    Uses its own database session to avoid tying the streaming lifecycle
    to a request-scoped session.
    """
    logger.info("Starting streaming analysis of top articles")

    async def event_stream():
        async with managed_session() as db:
            async for message in analyze_top_articles_stream(db):
                yield f"data: {message}\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")
