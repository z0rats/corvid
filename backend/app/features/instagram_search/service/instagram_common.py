"""Shared between Phase 1's profile lookup and Phase 2's follower/followee/post
scan: building an `Instaloader` instance and mapping its exceptions to
`AppHTTPException`. Kept in one place so the two don't drift on how a given
failure is classified.
"""

import logging
from typing import NoReturn

import instaloader

from app.core.exceptions import AppHTTPException
from app.features.instagram_search.config.instagram_search_config import (
    ERROR_PROFILE_NOT_FOUND,
    ERROR_RATE_LIMITED,
    ERROR_SESSION_REQUIRED,
    ERROR_UNAVAILABLE,
    ERROR_UPSTREAM_CHANGED,
)

logger = logging.getLogger(__name__)


def build_loader() -> instaloader.Instaloader:
    return instaloader.Instaloader(
        quiet=True,
        download_pictures=False,
        download_videos=False,
        download_video_thumbnails=False,
        download_geotags=False,
        download_comments=False,
        save_metadata=False,
        compress_json=False,
        # Avoid an extra request to the iphone-shaped endpoint from Profile.profile_pic_url/
        # Post.url when logged in - Phase 1/2 only ever need the lower-quality URL (link-only).
        iphone_support=False,
    )


def raise_mapped_instaloader_exception(exc: Exception, username: str) -> NoReturn:
    """Always raises: `exc` re-shaped as the matching `AppHTTPException` when it's
    one of Instaloader's own, or `exc` itself unchanged otherwise.

    Order matters: `TooManyRequestsException` and `QueryReturnedNotFoundException`
    are both subclasses of `ConnectionException`, so both are checked before it.
    """
    if isinstance(exc, instaloader.exceptions.ProfileNotExistsException):
        raise AppHTTPException(
            status_code=404,
            detail=f"Instagram profile '{username}' does not exist",
            error_code=ERROR_PROFILE_NOT_FOUND,
        ) from exc
    if isinstance(
        exc,
        (
            instaloader.exceptions.LoginRequiredException,
            instaloader.exceptions.PrivateProfileNotFollowedException,
        ),
    ):
        raise AppHTTPException(
            status_code=401,
            detail="This data requires an authorized Instagram session - configure one "
            "under Settings > API Keys",
            error_code=ERROR_SESSION_REQUIRED,
        ) from exc
    if isinstance(exc, instaloader.exceptions.TooManyRequestsException):
        raise AppHTTPException(
            status_code=429,
            detail="Instagram is rate-limiting this request, try again later",
            error_code=ERROR_RATE_LIMITED,
        ) from exc
    if isinstance(
        exc,
        (
            instaloader.exceptions.BadResponseException,
            instaloader.exceptions.QueryReturnedBadRequestException,
            instaloader.exceptions.QueryReturnedForbiddenException,
            instaloader.exceptions.QueryReturnedNotFoundException,
        ),
    ):
        raise AppHTTPException(
            status_code=502,
            detail="Instagram's response didn't match what this tool expects - "
            "it may have changed its API",
            error_code=ERROR_UPSTREAM_CHANGED,
        ) from exc
    if isinstance(exc, instaloader.exceptions.ConnectionException):
        raise AppHTTPException(
            status_code=503,
            detail="Could not reach Instagram right now",
            error_code=ERROR_UNAVAILABLE,
        ) from exc
    if isinstance(exc, instaloader.exceptions.InstaloaderException):
        logger.error("Unexpected Instaloader error for %s: %s", username, exc)
        raise AppHTTPException(
            status_code=502,
            detail="Unexpected error from Instagram",
            error_code=ERROR_UPSTREAM_CHANGED,
        ) from exc
    raise exc
