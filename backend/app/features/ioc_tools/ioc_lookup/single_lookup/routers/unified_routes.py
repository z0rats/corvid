import logging

from fastapi import APIRouter, Path, Query, HTTPException, Request, status
from app.core.exceptions import AppHTTPException

from app.core.config.rate_limit_config import limiter
from app.core.dependencies import ReadSessionDep
from app.features.ioc_tools.ioc_lookup.single_lookup.service.ioc_lookup_engine import (
    lookup_ioc, get_all_service_configs, build_service_definitions,
)
from app.features.ioc_tools.ioc_lookup.single_lookup.service.service_registry import get_service
from app.features.ioc_tools.ioc_lookup.single_lookup.utils.ioc_utils import determine_ioc_type, IOC_TYPES
from app.features.ioc_tools.ioc_lookup.schemas.lookup_schemas import (
    LookupResult,
    LookupStatus,
    ServicesResponse,
    ServiceDefinitionsResponse,
    IOCTypesResponse,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/ioc", tags=["IOC Lookup"])


@router.get(
    "/lookup/{service}",
    response_model=LookupResult,
    response_model_exclude_none=True,
    summary="Lookup a single IOC",
    description="Perform a lookup for a single IOC against a specified service",
    responses={
        400: {"description": "Invalid or unsupported IOC format, or service does not support this IOC type"},
        401: {"description": "Required API key is missing or inactive"},
        404: {"description": "Service not found"},
    },
)
@limiter.limit("30/minute")
async def unified_lookup(
    request: Request,
    db: ReadSessionDep,
    service: str = Path(..., description="Service name to query", min_length=1),
    ioc: str = Query(..., description="The IOC value to lookup"),
    ioc_type: str | None = Query(None, description="The IOC type (e.g., IPv4, Domain, MD5)"),
) -> LookupResult:
    detected_ioc_type = ioc_type or determine_ioc_type(ioc)
    if detected_ioc_type == IOC_TYPES['UNKNOWN']:
        raise AppHTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid or unsupported IOC format", error_code="IOC_INVALID_FORMAT")

    service_config = get_service(service)
    if service_config is None:
        raise AppHTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Service '{service}' not found.", error_code="IOC_SERVICE_NOT_FOUND")

    if detected_ioc_type not in service_config.get('supported_ioc_types', []):
        raise AppHTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Service '{service}' does not support IOC type '{detected_ioc_type}'.",
            error_code="IOC_UNSUPPORTED_TYPE",
        )

    result = await lookup_ioc(service, ioc, detected_ioc_type, db)

    if result is None:
        raise AppHTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Service '{service}' not found.", error_code="IOC_SERVICE_NOT_FOUND")

    if result.status == LookupStatus.UNAUTHORIZED:
        raise AppHTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=result.error or f"Required API key(s) for '{service}' are missing or inactive.",
            error_code="IOC_UNAUTHORIZED",
        )

    return result


@router.get(
    "/services",
    response_model=ServicesResponse,
    response_model_exclude_none=True,
    summary="Get available services",
    description="Get a list of all available lookup services with their configuration and status",
)
async def get_available_services(
    db: ReadSessionDep,
    ioc_type: str | None = Query(None, description="Filter services by IOC type"),
) -> ServicesResponse:
    all_services = await get_all_service_configs(db)

    if not ioc_type:
        return ServicesResponse(services=all_services)

    filtered_services = [
        s for s in all_services
        if ioc_type in s.supported_ioc_types
    ]

    return ServicesResponse(services=filtered_services)


@router.get(
    "/types",
    response_model=IOCTypesResponse,
    summary="Get supported IOC types",
    description="Get the dictionary of all supported IOC types",
)
def get_supported_ioc_types() -> IOCTypesResponse:
    return IOCTypesResponse(types=IOC_TYPES)


@router.get(
    "/service-definitions",
    response_model=ServiceDefinitionsResponse,
    summary="Get service definitions",
    description="Get complete service definitions including configuration and availability",
)
async def get_service_definitions(db: ReadSessionDep) -> ServiceDefinitionsResponse:
    return ServiceDefinitionsResponse(serviceDefinitions=await build_service_definitions(db))
