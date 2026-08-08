import logging

from fastapi import APIRouter, Request, status

from app.core.config.rate_limit_config import limiter
from app.core.dependencies import ReadSessionDep
from app.features.youtube.schemas.youtube_schemas import (
    YoutubeCommentsRequest,
    YoutubeCommentsResponse,
    YoutubeLookupRequest,
    YoutubeLookupResponse,
)
from app.features.youtube.service.youtube_comments_lookup_service import perform_youtube_comments_lookup
from app.features.youtube.service.youtube_lookup_service import perform_youtube_lookup

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/youtube", tags=["YouTube"])


@router.post(
    "/lookup",
    response_model=YoutubeLookupResponse,
    status_code=status.HTTP_200_OK,
    summary="Look up metadata for a YouTube video URL",
    description="Fetches keyless metadata (oEmbed + page-scraped Open Graph/schema.org fields, "
                 "standard thumbnail URLs) for a YouTube video, plus extended stats via the "
                 "YouTube Data API if a key is configured under Settings > API Keys",
)
@limiter.limit("30/minute")
async def lookup_youtube_video(
    request: Request, lookup_request: YoutubeLookupRequest, db: ReadSessionDep
) -> YoutubeLookupResponse:
    logger.info("YouTube metadata lookup requested - URL: %s", lookup_request.url)
    result = await perform_youtube_lookup(lookup_request, db)
    logger.info("YouTube metadata lookup completed - video_id: %s", result.video_id)
    return result


@router.post(
    "/comments",
    response_model=YoutubeCommentsResponse,
    status_code=status.HTTP_200_OK,
    summary="List or search a YouTube video's top-level comments",
    description="Lists a page of top-level comments (`order`/`page_token` for pagination), or, "
                 "when `query` is given, scans multiple pages server-side and returns comments "
                 "matching it by author or text - the YouTube Data API has no native comment-text "
                 "search. Requires a YouTube Data API key configured under Settings > API Keys.",
)
@limiter.limit("20/minute")
async def list_youtube_comments(
    request: Request, comments_request: YoutubeCommentsRequest, db: ReadSessionDep
) -> YoutubeCommentsResponse:
    logger.info(
        "YouTube comments requested - URL: %s, query: %s", comments_request.url, comments_request.query,
    )
    result = await perform_youtube_comments_lookup(comments_request, db)
    logger.info(
        "YouTube comments request completed - video_id: %s, comments: %s, truncated: %s",
        result.video_id, len(result.comments), result.truncated,
    )
    return result
