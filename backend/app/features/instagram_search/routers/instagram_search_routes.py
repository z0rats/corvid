import logging

from fastapi import APIRouter, Request, status

from app.core.config.rate_limit_config import limiter
from app.core.dependencies import ReadSessionDep
from app.features.instagram_search.schemas.instagram_search_schemas import (
    InstagramHealthResponse,
    InstagramProfileRequest,
    InstagramProfileResponse,
)
from app.features.instagram_search.service.instagram_health_service import get_health
from app.features.instagram_search.service.instagram_search_service import perform_profile_lookup

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/instagram-search", tags=["Instagram Search"])


@router.post(
    "/profile",
    response_model=InstagramProfileResponse,
    status_code=status.HTTP_200_OK,
    summary="Look up a public Instagram profile's metadata",
    description="Fetches profile metadata (bio, links, counters, verified/business/private "
    "flags) for an Instagram username, anonymously by default or through an "
    "authorized session imported under Settings > API Keys. A private profile "
    "the session doesn't follow still returns the metadata Instagram exposes, "
    "with `is_private: true`, rather than an error.",
)
@limiter.limit("5/minute")
async def lookup_instagram_profile(
    request: Request, profile_request: InstagramProfileRequest, db: ReadSessionDep
) -> InstagramProfileResponse:
    logger.info("Instagram profile lookup requested - username: %s", profile_request.username)
    result = await perform_profile_lookup(profile_request, db)
    logger.info("Instagram profile lookup completed - username: %s", result.username)
    return result


@router.get(
    "/health",
    response_model=InstagramHealthResponse,
    status_code=status.HTTP_200_OK,
    summary="Check the Instagram module's health",
    description="Reports the installed Instaloader version and whether an Instagram "
    "session is currently configured and well-formed.",
)
async def instagram_health(db: ReadSessionDep) -> InstagramHealthResponse:
    return await get_health(db)
