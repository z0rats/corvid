"""Looks up public Instagram profile metadata via Instaloader - anonymously by
default, or through an optional imported browser-session cookie (see
`instagram_session_service.py`). Read-only: every Instaloader download_*/
save_metadata flag is off, so nothing is written to disk and no media is
fetched, only the profile JSON node itself.

Instaloader is synchronous (`requests`-based); the actual call runs in a worker
thread via `asyncio.to_thread` and every `Profile` field read happens inside
that same thread, since some of them (`profile_pic_url` with `iphone_support`
enabled) can trigger their own blocking network call - so we disable
`iphone_support` and finish reading the profile before returning to the event
loop, rather than handing a lazily-evaluating `Profile` object back to it.

Instaloader's `requests` client only ever talks to Instagram's own fixed hosts
(never a user-supplied URL), so this doesn't go through `app.core.security.
ssrf_guard.safe_get` - there's nothing for it to validate.
"""

import asyncio
import logging
from datetime import UTC, datetime
from typing import Any

import instaloader
from sqlalchemy.ext.asyncio import AsyncSession

from app.features.instagram_search.config.instagram_search_config import (
    SESSION_OWNER_PLACEHOLDER,
)
from app.features.instagram_search.schemas.instagram_search_schemas import (
    InstagramProfileRequest,
    InstagramProfileResponse,
)
from app.features.instagram_search.service.instagram_common import (
    build_loader,
    raise_mapped_instaloader_exception,
)
from app.features.instagram_search.service.instagram_session_service import get_session_dict

logger = logging.getLogger(__name__)


def _fetch_profile_sync(username: str, session_data: dict[str, str] | None) -> dict[str, Any]:
    """Blocking Instaloader call - runs off the event loop via `asyncio.to_thread`.

    Reads every field of the returned `Profile` here rather than handing it back
    to the caller, since `Profile` properties can lazily trigger their own
    network calls.
    """
    loader = build_loader()
    if session_data:
        loader.context.load_session(SESSION_OWNER_PLACEHOLDER, session_data)

    profile = instaloader.Profile.from_username(loader.context, username)
    return {
        "username": profile.username,
        "userid": profile.userid,
        "full_name": profile.full_name,
        "biography": profile.biography,
        "biography_hashtags": list(profile.biography_hashtags),
        "biography_mentions": list(profile.biography_mentions),
        "external_url": profile.external_url,
        "followers": profile.followers,
        "followees": profile.followees,
        "mediacount": profile.mediacount,
        "igtvcount": profile.igtvcount,
        "is_private": profile.is_private,
        "is_verified": profile.is_verified,
        "is_business_account": profile.is_business_account,
        "business_category_name": profile.business_category_name,
        "has_public_story": profile.has_public_story,
        "has_highlight_reels": profile.has_highlight_reels,
        "profile_pic_url": profile.profile_pic_url,
    }


async def perform_profile_lookup(
    request: InstagramProfileRequest, db: AsyncSession
) -> InstagramProfileResponse:
    """Look up an Instagram profile's public metadata.

    Raises:
        AppHTTPException: mapped from Instaloader's exceptions - profile not
            found, an authorized session is required, Instagram is rate-limiting
            this request, it's unreachable, or its response shape changed.
    """
    session_data = await get_session_dict(db)
    mode = "session" if session_data else "anonymous"

    try:
        fields = await asyncio.to_thread(_fetch_profile_sync, request.username, session_data)
    except instaloader.exceptions.InstaloaderException as e:
        raise_mapped_instaloader_exception(e, request.username)

    logger.info("Instagram profile lookup completed for %s (mode=%s)", request.username, mode)
    return InstagramProfileResponse(
        **fields,
        mode=mode,
        timestamp=datetime.now(UTC),
    )
