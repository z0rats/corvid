from fastapi import APIRouter

from app.core.dependencies import SessionDep
from app.core.settings.ai_settings.schemas.ai_settings_schemas import (
    AISettingsResponse,
    AISettingsUpdate,
    AvailableModelsResponse,
    AvailableModel,
)
from app.core.settings.ai_settings.service.ai_settings_service import (
    get_or_create_ai_settings,
    update_ai_settings_values,
)
from app.utils.llm_service import get_available_models

router = APIRouter(prefix="/api/settings/ai", tags=["AI Settings"])


@router.get(
    "",
    response_model=AISettingsResponse,
    summary="Get AI settings",
    description="Retrieve current AI / LLM default model settings",
)
async def get_ai_settings_endpoint(db: SessionDep) -> AISettingsResponse:
    return await get_or_create_ai_settings(db)


@router.put(
    "",
    response_model=AISettingsResponse,
    summary="Update AI settings",
    description="Update AI / LLM default model settings",
)
async def update_ai_settings_endpoint(
    settings_update: AISettingsUpdate,
    db: SessionDep,
) -> AISettingsResponse:
    return await update_ai_settings_values(db, settings_update)


@router.get(
    "/available-models",
    response_model=AvailableModelsResponse,
    summary="Get available models",
    description="Get list of LLM models that are available based on configured API keys",
)
async def get_available_models_endpoint(db: SessionDep) -> AvailableModelsResponse:
    models = await get_available_models(db)
    return AvailableModelsResponse(
        models=[AvailableModel(**m) for m in models]
    )
