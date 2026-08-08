"""Orchestrates a YouTube video metadata lookup: oEmbed (required) + page-scrape
enrichment (best-effort) + an optional YouTube Data API tier (best-effort, only if
a key is configured under Settings > API Keys).
"""
import logging
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import AppHTTPException
from app.features.youtube.config.youtube_config import build_thumbnail_urls
from app.features.youtube.schemas.youtube_schemas import (
    YoutubeApiData,
    YoutubeLookupRequest,
    YoutubeLookupResponse,
    YoutubeOembedData,
    YoutubePageMetadata,
)
from app.features.youtube.service.youtube_api_key_service import get_youtube_api_key
from app.features.youtube.service.youtube_api_service import fetch_video_api_data
from app.features.youtube.service.youtube_oembed_service import fetch_oembed_data
from app.features.youtube.service.youtube_page_service import fetch_page_metadata
from app.features.youtube.utils.youtube_url_utils import canonical_video_url, extract_video_id

logger = logging.getLogger(__name__)


async def perform_youtube_lookup(request: YoutubeLookupRequest, db: AsyncSession) -> YoutubeLookupResponse:
    """Look up metadata for a YouTube video URL.

    Raises:
        AppHTTPException: When the URL isn't a recognized YouTube video link, or
            the video is missing/private/embed-disabled.
    """
    video_id = extract_video_id(request.url)
    if not video_id:
        raise AppHTTPException(
            status_code=400,
            detail="Not a recognized YouTube video URL",
            error_code="YOUTUBE_INVALID_URL",
        )

    video_url = canonical_video_url(video_id)
    logger.info("Starting YouTube metadata lookup for video: %s", video_id)

    oembed_raw = await fetch_oembed_data(video_url)
    oembed = YoutubeOembedData(
        title=oembed_raw.get("title"),
        author_name=oembed_raw.get("author_name"),
        author_url=oembed_raw.get("author_url"),
        thumbnail_url=oembed_raw.get("thumbnail_url"),
        html=oembed_raw.get("html"),
        provider_name=oembed_raw.get("provider_name"),
        width=oembed_raw.get("width"),
        height=oembed_raw.get("height"),
    )

    page_fields = await fetch_page_metadata(video_url)
    page_metadata = _map_page_metadata(page_fields) if page_fields else None

    api_key = await get_youtube_api_key(db)
    api_data = None
    if api_key:
        api_raw = await fetch_video_api_data(video_id, api_key)
        api_data = _map_api_data(api_raw) if api_raw else None

    response = YoutubeLookupResponse(
        video_id=video_id,
        video_url=video_url,
        oembed=oembed,
        page_metadata=page_metadata,
        thumbnails=build_thumbnail_urls(video_id),
        api_data=api_data,
        api_configured=api_key is not None,
    )
    logger.info("YouTube metadata lookup completed for video: %s", video_id)
    return response


def _map_page_metadata(fields: dict[str, str]) -> YoutubePageMetadata:
    return YoutubePageMetadata(
        description=fields.get("description") or fields.get("og:description"),
        duration=fields.get("duration"),
        date_published=fields.get("datePublished"),
        upload_date=fields.get("uploadDate"),
        genre=fields.get("genre"),
        channel_id=fields.get("channelId"),
        keywords=fields.get("keywords"),
        is_family_friendly=fields.get("isFamilyFriendly"),
        interaction_count=fields.get("interactionCount"),
    )


def _map_api_data(item: dict[str, Any]) -> YoutubeApiData:
    snippet = item.get("snippet") or {}
    content_details = item.get("contentDetails") or {}
    statistics = item.get("statistics") or {}
    video_status = item.get("status") or {}
    return YoutubeApiData(
        published_at=snippet.get("publishedAt"),
        channel_id=snippet.get("channelId"),
        channel_title=snippet.get("channelTitle"),
        description=snippet.get("description"),
        tags=snippet.get("tags") or [],
        category_id=snippet.get("categoryId"),
        duration=content_details.get("duration"),
        definition=content_details.get("definition"),
        view_count=statistics.get("viewCount"),
        like_count=statistics.get("likeCount"),
        comment_count=statistics.get("commentCount"),
        privacy_status=video_status.get("privacyStatus"),
    )
