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
from app.core.settings.settings_router_factory import build_singleton_settings_router
from app.utils.llm_service import get_available_models

router = build_singleton_settings_router(
    prefix="/api/settings/ai",
    tags=["AI Settings"],
    response_schema=AISettingsResponse,
    update_schema=AISettingsUpdate,
    get_service=get_or_create_ai_settings,
    update_service=update_ai_settings_values,
)


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
