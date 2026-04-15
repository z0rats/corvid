from typing import Any
from fastapi import APIRouter, Query

from app.core.dependencies import ReadSessionDep
from app.core.settings.api_keys.config.service_config import ServiceCategory, ServiceTier
from app.core.settings.api_keys.service.service_config_service import (
    get_services_configuration,
    get_single_service_configuration,
    get_service_categories,
    get_service_tiers,
    get_supported_ioc_types,
    get_services_for_ioc_type_service
)


router = APIRouter()


@router.get("/api/services/config", response_model=dict[str, dict[str, Any]], tags=["Service Configuration"])
async def get_services_config(
    db: ReadSessionDep,
    category: ServiceCategory | None = Query(None, description="Filter by service category"),
    tier: ServiceTier | None = Query(None, description="Filter by service tier"),
    ioc_type: str | None = Query(None, description="Filter by supported IOC type"),
) -> dict[str, dict[str, Any]]:
    """
    Get service configuration data.

    - **category**: Filter by service category (threat_intelligence, security_scanning, etc.)
    - **tier**: Filter by service tier (free, paid, freemium)
    - **ioc_type**: Filter by supported IOC type (IPv4, Domain, Email, etc.)
    """
    return await get_services_configuration(db, category, tier, ioc_type)


@router.get("/api/services/config/{service_key}", response_model=dict[str, Any], tags=["Service Configuration"])
async def get_service_config(service_key: str, db: ReadSessionDep) -> dict[str, Any]:
    """
    Get configuration for a specific service.

    - **service_key**: The unique identifier for the service
    """
    return await get_single_service_configuration(db, service_key)


@router.get("/api/services/categories", response_model=list[str], tags=["Service Configuration"])
async def get_service_categories_endpoint() -> list[str]:
    """Get all available service categories."""
    return await get_service_categories()


@router.get("/api/services/tiers", response_model=list[str], tags=["Service Configuration"])
async def get_service_tiers_endpoint() -> list[str]:
    """Get all available service tiers."""
    return await get_service_tiers()


@router.get("/api/services/ioc-types", response_model=list[str], tags=["Service Configuration"])
async def get_supported_ioc_types_endpoint() -> list[str]:
    """Get all supported IOC types across all services."""
    return await get_supported_ioc_types()


@router.get("/api/services/for-ioc/{ioc_type}", response_model=dict[str, dict[str, Any]], tags=["Service Configuration"])
async def get_services_for_ioc(ioc_type: str, db: ReadSessionDep) -> dict[str, dict[str, Any]]:
    """
    Get all services that support a specific IOC type.

    - **ioc_type**: The IOC type to filter by (IPv4, Domain, Email, etc.)
    """
    return await get_services_for_ioc_type_service(db, ioc_type)
