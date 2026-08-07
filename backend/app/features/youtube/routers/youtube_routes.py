import logging

from fastapi import APIRouter, Request, status

from app.core.config.rate_limit_config import limiter
from app.core.dependencies import ReadSessionDep
from app.features.youtube.schemas.youtube_schemas import YoutubeLookupRequest, YoutubeLookupResponse
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
