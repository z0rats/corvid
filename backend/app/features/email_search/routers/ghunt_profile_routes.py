import logging

from fastapi import APIRouter, Request

from app.core.config.rate_limit_config import limiter
from app.core.dependencies import ReadSessionDep, SessionDep
from app.core.settings.api_keys.schemas.api_keys_settings_schemas import ApikeyStateResponse
from app.features.email_search.schemas.ghunt_schemas import (
    GhuntHealthResponse,
    GhuntProfileRequest,
    GhuntProfileResponse,
    GhuntSessionSaveRequest,
)
from app.features.email_search.service.ghunt_profile_service import (
    get_ghunt_health,
    run_ghunt_profile,
)
from app.features.email_search.service.ghunt_session_service import save_ghunt_session

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/email-search/ghunt-profile", tags=["Email Search"])


@router.post(
    "",
    response_model=GhuntProfileResponse,
    summary="Look up a Google account profile by email (GHunt)",
    description=(
        "Runs GHunt against the given email using the configured session. Explicit action only "
        "- the request is made to Google from the analyst's own configured account, and GHunt's "
        "own account is single-flight (one lookup at a time)."
    ),
    responses={
        409: {"description": "No session configured, or the stored session is invalid/expired"}
    },
)
@limiter.limit("5/minute")
async def lookup_ghunt_profile(
    request: Request, profile_request: GhuntProfileRequest, db: SessionDep
) -> GhuntProfileResponse:
    logger.info("GHunt profile lookup requested for an email address")
    result = await run_ghunt_profile(db, profile_request.email)
    logger.info("GHunt profile lookup completed - gaia_id: %s", result.gaia_id)
    return result


@router.get(
    "/health",
    response_model=GhuntHealthResponse,
    summary="Get GHunt tool status",
    description=(
        "Whether the GHunt CLI is installed, its version, and whether a session is configured"
    ),
)
async def read_ghunt_health(db: ReadSessionDep) -> GhuntHealthResponse:
    return await get_ghunt_health(db)


@router.put(
    "/session",
    response_model=ApikeyStateResponse,
    summary="Store a GHunt session",
    description=(
        "Validates the pasted session blob's structure (base64 -> JSON -> expected keys) "
        "without ever running GHunt, then stores it the same way as any other API key. The "
        "value itself is never returned in the response."
    ),
    responses={400: {"description": "Not a structurally valid GHunt session"}},
)
async def save_session(
    request: Request, save_request: GhuntSessionSaveRequest, db: SessionDep
) -> ApikeyStateResponse:
    result = await save_ghunt_session(db, save_request.value)
    logger.info("GHunt session saved")
    return result
