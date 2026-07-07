"""Email Search (mailcat) settings routes - timeout, concurrency, proxy/Tor, optional checkers"""

import logging

from fastapi import APIRouter

from app.core.dependencies import ReadSessionDep, SessionDep
from app.core.settings.email_search.crud.email_search_settings_crud import (
    get_email_search_config as crud_get_config,
    update_email_search_config as crud_update_config,
)
from app.core.settings.email_search.schemas.email_search_settings_schemas import (
    EmailSearchConfigSchema,
    EmailSearchConfigUpdateSchema,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/settings/email-search", tags=["Email Search Settings"])


@router.get(
    "",
    response_model=EmailSearchConfigSchema,
    response_model_exclude_none=True,
    summary="Get email search config",
    description="Get email search (mailcat) configuration",
)
async def get_email_search_config(db: ReadSessionDep) -> EmailSearchConfigSchema:
    """Get current email search configuration"""
    return EmailSearchConfigSchema.model_validate(await crud_get_config(db))


@router.put(
    "",
    response_model=EmailSearchConfigSchema,
    response_model_exclude_none=True,
    summary="Update email search config",
    description="Update email search (mailcat) configuration",
)
async def update_email_search_config(
    config_data: EmailSearchConfigUpdateSchema, db: SessionDep
) -> EmailSearchConfigSchema:
    """Update email search configuration"""
    updated_config = await crud_update_config(db, config_data)
    logger.info("Updated email search configuration.")
    return EmailSearchConfigSchema.model_validate(updated_config)
