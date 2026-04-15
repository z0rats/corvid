"""Module settings API routes"""

from fastapi import APIRouter, status

from app.core.dependencies import ReadSessionDep, SessionDep
from app.core.settings.modules.schemas.modules_settings_schemas import (
    ModuleSettingsResponse,
    ModuleSettingsCreate,
    ModuleSettingsUpdate,
    ModuleStatusUpdate
)
from app.core.settings.modules.service.modules_settings_service import (
    get_all_modules_settings,
    get_module_setting,
    create_new_module_setting,
    update_module_setting,
    update_module_status,
    delete_module_setting_by_name
)

router = APIRouter(prefix="/api/settings/modules", tags=["Settings"])


@router.get(
    "",
    response_model=list[ModuleSettingsResponse],
    summary="Get all module settings",
    description="Retrieve all module settings from the database"
)
async def read_all_module_settings(db: ReadSessionDep) -> list[ModuleSettingsResponse]:
    return await get_all_modules_settings(db)


@router.get(
    "/{module_name}",
    response_model=ModuleSettingsResponse,
    summary="Get specific module setting",
    description="Retrieve a specific module setting by name",
    responses={
        400: {"description": "Invalid module name format"},
        404: {"description": "Module setting not found"},
    },
)
async def read_module_setting(module_name: str, db: ReadSessionDep) -> ModuleSettingsResponse:
    return await get_module_setting(db, module_name)


@router.post(
    "",
    response_model=ModuleSettingsResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create new module setting",
    description="Create a new module setting with specified configuration",
    responses={
        400: {"description": "Invalid module name or enabled status"},
        409: {"description": "Module setting already exists"},
    },
)
async def create_module_setting_endpoint(
    module_data: ModuleSettingsCreate,
    db: SessionDep
) -> ModuleSettingsResponse:
    return await create_new_module_setting(db, module_data)


@router.put(
    "/{module_name}",
    response_model=ModuleSettingsResponse,
    summary="Update module setting",
    description="Update an existing module setting",
    responses={
        400: {"description": "Invalid module name or enabled status"},
        404: {"description": "Module setting not found"},
    },
)
async def update_module_setting_endpoint(
    module_name: str,
    update_data: ModuleSettingsUpdate,
    db: SessionDep
) -> ModuleSettingsResponse:
    return await update_module_setting(db, module_name, update_data)


@router.patch(
    "/{module_name}/status",
    response_model=ModuleSettingsResponse,
    summary="Update module status",
    description="Enable or disable a specific module",
    responses={400: {"description": "Invalid module name format"}},
)
async def update_module_status_endpoint(
    module_name: str,
    status_data: ModuleStatusUpdate,
    db: SessionDep
) -> ModuleSettingsResponse:
    return await update_module_status(db, module_name, status_data)


@router.delete(
    "/{module_name}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete module setting",
    description="Delete a module setting from the database",
    responses={
        400: {"description": "Invalid module name format"},
        404: {"description": "Module setting not found"},
    },
)
async def delete_module_setting_endpoint(
    module_name: str,
    db: SessionDep
) -> None:
    await delete_module_setting_by_name(db, module_name)
