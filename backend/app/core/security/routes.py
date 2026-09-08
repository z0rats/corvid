"""Route for regenerating the shared API access token - see access_control.py's
module docstring for the token model this rotates."""

from fastapi import APIRouter

from app.core.alerts.service.alerts_service import raise_alert
from app.core.dependencies import SessionDep
from app.core.exceptions import ApplicationError
from app.core.security.access_control import AccessTokenFixedError, regenerate_access_token
from app.core.security.schemas import AccessTokenRegenerateResponse

router = APIRouter(prefix="/api/settings/access-token", tags=["Access Token"])


@router.post(
    "/regenerate",
    response_model=AccessTokenRegenerateResponse,
    summary="Regenerate the shared API access token",
    description=(
        "Generates a new access token and invalidates the old one immediately. "
        "Every other browser tab/device and the browser extension are signed out "
        "on their next request and need the new token entered manually."
    ),
)
async def regenerate_access_token_endpoint(db: SessionDep) -> AccessTokenRegenerateResponse:
    try:
        new_token = regenerate_access_token()
    except AccessTokenFixedError as exc:
        raise ApplicationError(
            str(exc), status_code=409, error_code="ACCESS_TOKEN_FIXED_BY_ENV"
        ) from exc

    await raise_alert(
        db,
        module="security",
        title="Access token regenerated",
        message=(
            "The shared API access token was regenerated. Other sessions and the "
            "browser extension will need the new token."
        ),
        telegram_category="security",
    )
    return AccessTokenRegenerateResponse(access_token=new_token)
