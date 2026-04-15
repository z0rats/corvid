from typing import Annotated

from fastapi import APIRouter, HTTPException, Path, status

from app.core.dependencies import ReadSessionDep, SessionDep
from app.core.settings.api_keys.schemas.api_keys_settings_schemas import (
    ApikeySchema,
    ApikeyCreateRequest,
    ApikeyUpdateRequest,
    ApikeyStateResponse,
    ApikeyBulkLookupStateResponse,
    DeleteApikeyResponse,
    UpdateActiveStatusRequest,
    UpdateBulkLookupStatusRequest,
)
from app.core.settings.api_keys.service.api_keys_service import (
    create_apikey_service,
    delete_apikey_service,
    get_all_apikeys_active_status,
    get_apikey_active_status,
    update_apikey_active_status,
    get_all_apikeys_bulk_lookup_status,
    get_apikey_bulk_lookup_status,
    update_apikey_bulk_lookup_status,
    upsert_apikey_bulk_lookup_status,
    update_apikey_service,
    get_all_apikeys_configured_status,
)


router = APIRouter(prefix="/api/apikeys", tags=["Settings"])

ApiKeyName = Annotated[str, Path(min_length=1, max_length=100, description="API key provider name")]


# --- Collection routes (no path parameters) ---

@router.post(
    "",
    response_model=ApikeySchema,
    status_code=status.HTTP_201_CREATED,
    summary="Create API key",
    description="Create a new API key entry for an external service",
    responses={409: {"description": "API key already exists"}},
)
async def create_apikey(apikey: ApikeyCreateRequest, db: SessionDep) -> ApikeySchema:
    result = await create_apikey_service(db, apikey)
    if result is None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="API key already exists")
    return result


@router.get(
    "/is_active",
    response_model=dict[str, bool],
    summary="Get all API keys active status",
    description="Get the active/inactive status for all API keys",
)
async def get_all_apikeys_is_active(db: ReadSessionDep) -> dict[str, bool]:
    return await get_all_apikeys_active_status(db)


@router.get(
    "/bulk_ioc_lookup",
    response_model=dict[str, bool],
    summary="Get all API keys bulk lookup status",
    description="Get the bulk lookup enabled/disabled status for all API keys, including keyless services",
)
async def get_all_apikeys_bulk_lookup(db: ReadSessionDep) -> dict[str, bool]:
    from app.features.ioc_tools.ioc_lookup.single_lookup.service.service_registry import get_all_services
    result = await get_all_apikeys_bulk_lookup_status(db)
    for service_name, config in get_all_services().items():
        if not config.get('api_key_name') and not config.get('api_key_names'):
            result.setdefault(service_name, True)
    return result


@router.get(
    "/configured",
    response_model=dict[str, bool],
    summary="Get all API keys configured status",
    description="Get the configuration status (has actual key value) for all API keys",
)
async def get_all_apikeys_configured(db: ReadSessionDep) -> dict[str, bool]:
    return await get_all_apikeys_configured_status(db)


# --- Item routes (with {name} path parameter) ---

@router.get(
    "/{name}/is_active",
    response_model=ApikeyStateResponse,
    summary="Get API key active status",
    description="Get the active status for a specific API key",
    responses={404: {"description": "API key not found"}},
)
async def get_apikey_is_active(name: ApiKeyName, db: ReadSessionDep) -> ApikeyStateResponse:
    is_active = await get_apikey_active_status(db, name)
    if is_active is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="API key not found")
    return ApikeyStateResponse(name=name, is_active=is_active)


@router.patch(
    "/{name}/is_active",
    response_model=ApikeySchema,
    summary="Update API key active status",
    description="Update the active/inactive status for a specific API key",
    responses={404: {"description": "API key not found"}},
)
async def update_apikey_is_active(name: ApiKeyName, data: UpdateActiveStatusRequest, db: SessionDep) -> ApikeySchema:
    result = await update_apikey_active_status(db, name, data.is_active)
    if result is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="API key not found")
    return result


@router.get(
    "/{name}/bulk_ioc_lookup",
    response_model=ApikeyBulkLookupStateResponse,
    summary="Get API key bulk lookup status",
    description="Get the bulk lookup status for a specific API key",
    responses={404: {"description": "API key not found"}},
)
async def get_apikey_bulk_lookup(name: ApiKeyName, db: ReadSessionDep) -> ApikeyBulkLookupStateResponse:
    bulk_ioc_lookup = await get_apikey_bulk_lookup_status(db, name)
    if bulk_ioc_lookup is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="API key not found")
    return ApikeyBulkLookupStateResponse(name=name, bulk_ioc_lookup=bulk_ioc_lookup)


@router.patch(
    "/{name}/bulk_ioc_lookup",
    response_model=ApikeySchema,
    summary="Update API key bulk lookup status",
    description="Update the bulk lookup enabled/disabled status for a specific API key. Creates a record for keyless services if none exists.",
)
async def update_apikey_bulk_lookup(name: ApiKeyName, data: UpdateBulkLookupStatusRequest, db: SessionDep) -> ApikeySchema:
    result = await update_apikey_bulk_lookup_status(db, name, data.bulk_ioc_lookup)
    if result is not None:
        return result
    from app.features.ioc_tools.ioc_lookup.single_lookup.service.service_registry import get_service
    service_config = get_service(name)
    if service_config and not service_config.get('api_key_name') and not service_config.get('api_key_names'):
        return await upsert_apikey_bulk_lookup_status(db, name, data.bulk_ioc_lookup)
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="API key not found")


@router.patch(
    "/{name}",
    response_model=ApikeySchema,
    summary="Update API key",
    description="Partially update an existing API key's value, active status, and bulk lookup setting",
    responses={404: {"description": "API key not found"}},
)
async def update_apikey(name: ApiKeyName, apikey: ApikeyUpdateRequest, db: SessionDep) -> ApikeySchema:
    result = await update_apikey_service(db, name, apikey)
    if result is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="API key not found")
    return result


@router.delete(
    "/{name}",
    response_model=DeleteApikeyResponse,
    summary="Delete API key",
    description="Delete an API key by its provider name",
    responses={404: {"description": "API key not found"}},
)
async def delete_apikey(name: ApiKeyName, db: SessionDep) -> DeleteApikeyResponse:
    result = await delete_apikey_service(db, name)
    if result is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="API key not found")
    return result
