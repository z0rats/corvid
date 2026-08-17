"""Orchestrates YouTube comment listing/search.

Two modes, both requiring a YouTube Data API key configured under Settings > API Keys -
comments have no keyless tier to fall back to, unlike /lookup:
- No `query`: a plain single-page listing, `page_token` drives "load more".
- `query` given: the Data API has no native comment-text search, so this scans multiple
  pages server-side (capped by COMMENTS_SEARCH_MAX_PAGES/COMMENTS_SEARCH_MAX_RESULTS),
  filtering by author/text substring match.
"""

import logging
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import AppHTTPException
from app.features.youtube.config.youtube_config import (
    COMMENTS_LISTING_PAGE_SIZE,
    COMMENTS_SEARCH_MAX_PAGES,
    COMMENTS_SEARCH_MAX_RESULTS,
    COMMENTS_SEARCH_PAGE_SIZE,
)
from app.features.youtube.schemas.youtube_schemas import (
    YoutubeComment,
    YoutubeCommentsRequest,
    YoutubeCommentsResponse,
)
from app.features.youtube.service.youtube_api_key_service import get_youtube_api_key
from app.features.youtube.service.youtube_api_service import fetch_comment_threads
from app.features.youtube.utils.youtube_url_utils import extract_video_id

logger = logging.getLogger(__name__)


async def perform_youtube_comments_lookup(
    request: YoutubeCommentsRequest, db: AsyncSession
) -> YoutubeCommentsResponse:
    """List or search a YouTube video's top-level comments.

    Raises:
        AppHTTPException: When the URL isn't a recognized YouTube video link, or no
            YouTube Data API key is configured.
    """
    video_id = extract_video_id(request.url)
    if not video_id:
        raise AppHTTPException(
            status_code=400,
            detail="Not a recognized YouTube video URL",
            error_code="YOUTUBE_INVALID_URL",
        )

    api_key = await get_youtube_api_key(db)
    if not api_key:
        raise AppHTTPException(
            status_code=400,
            detail=(
                "A YouTube Data API key is required for comments. Add one under "
                "Settings > API Keys."
            ),
            error_code="YOUTUBE_COMMENTS_NOT_CONFIGURED",
        )

    if request.query:
        return await _search_comments(video_id, api_key, request)
    return await _list_comments(video_id, api_key, request)


async def _list_comments(
    video_id: str, api_key: str, request: YoutubeCommentsRequest
) -> YoutubeCommentsResponse:
    raw = await fetch_comment_threads(
        video_id,
        api_key,
        order=request.order,
        page_token=request.page_token,
        max_results=COMMENTS_LISTING_PAGE_SIZE,
    )
    comments = [_map_comment_thread(item) for item in raw.get("items", [])]
    return YoutubeCommentsResponse(
        video_id=video_id,
        comments=comments,
        next_page_token=raw.get("nextPageToken"),
        pages_scanned=1,
    )


async def _search_comments(
    video_id: str, api_key: str, request: YoutubeCommentsRequest
) -> YoutubeCommentsResponse:
    query = request.query.lower()
    matches: list[YoutubeComment] = []
    page_token = request.page_token
    pages_scanned = 0
    exhausted = False

    while pages_scanned < COMMENTS_SEARCH_MAX_PAGES and len(matches) < COMMENTS_SEARCH_MAX_RESULTS:
        raw = await fetch_comment_threads(
            video_id,
            api_key,
            order=request.order,
            page_token=page_token,
            max_results=COMMENTS_SEARCH_PAGE_SIZE,
        )
        pages_scanned += 1

        for item in raw.get("items", []):
            comment = _map_comment_thread(item)
            if _matches_query(comment, query):
                matches.append(comment)
                if len(matches) >= COMMENTS_SEARCH_MAX_RESULTS:
                    break

        page_token = raw.get("nextPageToken")
        if not page_token:
            exhausted = True
            break

    return YoutubeCommentsResponse(
        video_id=video_id,
        comments=matches,
        next_page_token=page_token,
        query=request.query,
        truncated=not exhausted,
        pages_scanned=pages_scanned,
    )


def _matches_query(comment: YoutubeComment, query_lower: str) -> bool:
    if query_lower in comment.text.lower():
        return True
    return bool(comment.author_display_name) and query_lower in comment.author_display_name.lower()


def _map_comment_thread(item: dict[str, Any]) -> YoutubeComment:
    thread_snippet = item.get("snippet", {})
    top_level = thread_snippet.get("topLevelComment", {})
    snippet = top_level.get("snippet", {})
    return YoutubeComment(
        comment_id=top_level.get("id") or item.get("id", ""),
        author_display_name=snippet.get("authorDisplayName"),
        author_channel_url=snippet.get("authorChannelUrl"),
        author_profile_image_url=snippet.get("authorProfileImageUrl"),
        text=snippet.get("textDisplay", ""),
        like_count=snippet.get("likeCount", 0),
        reply_count=thread_snippet.get("totalReplyCount", 0),
        published_at=snippet.get("publishedAt"),
        updated_at=snippet.get("updatedAt"),
    )
