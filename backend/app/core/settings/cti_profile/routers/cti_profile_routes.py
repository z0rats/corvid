"""
CTI Profile Settings Routes

FastAPI routes for CTI (Cyber Threat Intelligence) profile settings management.
"""

import logging
from typing import Literal, NoReturn

from fastapi import status

from app.core.exceptions import AppHTTPException
from app.core.settings.cti_profile.schemas.cti_profile_schemas import (
    CTISettingsResponse,
    CTISettingsUpdate,
)
from app.core.settings.cti_profile.service.cti_profile_service import (
    get_cti_profile_settings,
    update_cti_profile_settings,
)
from app.core.settings.settings_router_factory import build_singleton_settings_router

logger = logging.getLogger(__name__)

_ERROR_DETAIL = {
    "get": ("Failed to retrieve CTI profile settings", "CTI_SETTINGS_RETRIEVE_FAILED"),
    "update": ("Failed to update CTI profile settings", "CTI_SETTINGS_UPDATE_FAILED"),
}


def _map_cti_error(exc: Exception, op: Literal["get", "update"]) -> NoReturn:
    """Map get_cti_profile_settings/update_cti_profile_settings errors to AppHTTPException.

    Preserves the pre-factory behavior: a ValueError (settings validation
    failure) becomes 400, anything else becomes 500 - with distinct
    detail/error_code per operation.
    """
    if isinstance(exc, ValueError):
        logger.warning("Validation error during CTI settings %s: %s", op, str(exc))
        raise AppHTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid settings data: {str(exc)}",
            error_code="CTI_SETTINGS_INVALID",
        ) from exc

    detail, error_code = _ERROR_DETAIL[op]
    logger.error("Unexpected error during CTI settings %s: %s", op, str(exc))
    raise AppHTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail=detail,
        error_code=error_code,
    ) from exc


router = build_singleton_settings_router(
    prefix="/api/settings/cti",
    tags=["CTI Profile Settings"],
    response_schema=CTISettingsResponse,
    update_schema=CTISettingsUpdate,
    get_service=get_cti_profile_settings,
    update_service=update_cti_profile_settings,
    on_error=_map_cti_error,
)
