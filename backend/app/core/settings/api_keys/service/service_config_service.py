import logging
from typing import Any

from fastapi import HTTPException, status
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.settings.api_keys.config.service_config import (
    ServiceDefinition,
    ServiceCategory,
    ServiceTier,
    get_service_definition,
    get_all_service_definitions,
    get_services_by_category,
    get_services_by_tier,
    get_services_for_ioc_type,
    get_required_keys_for_service
)
from app.core.settings.api_keys.crud.api_keys_settings_crud import get_apikeys
from app.core.settings.api_keys.config.create_defaults import get_service_status_summary

logger = logging.getLogger(__name__)


async def get_services_configuration(
    db: AsyncSession,
    category: ServiceCategory | None = None,
    tier: ServiceTier | None = None,
    ioc_type: str | None = None
) -> dict[str, dict[str, Any]]:
    """Get service configuration data with optional filters."""
    try:
        services = get_all_service_definitions()

        if category:
            services = get_services_by_category(category)
        if tier:
            services = get_services_by_tier(tier)
        if ioc_type:
            services = get_services_for_ioc_type(ioc_type)

        api_keys = await get_apikeys(db)
        api_key_states = {apikey.name: apikey.is_active for apikey in api_keys}

        response = {}
        for key, service in services.items():
            service_dict = service.to_dict()
            service_dict["api_key_status"] = _build_api_key_status(service, api_key_states)
            service_dict["available"] = _calculate_service_availability(service, api_key_states)
            response[key] = service_dict

        logger.info("Retrieved %s service configurations", len(response))
        return response

    except SQLAlchemyError as e:
        logger.error("Database error retrieving service configuration: %s", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve service configuration"
        )
    except Exception as e:
        logger.error("Unexpected error retrieving service configuration: %s", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


async def get_single_service_configuration(db: AsyncSession, service_key: str) -> dict[str, Any]:
    """Get configuration for a specific service."""
    try:
        service = get_service_definition(service_key)
        if not service:
            logger.error("Service not found: %s", service_key)
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Service '{service_key}' not found"
            )

        api_keys = await get_apikeys(db)
        api_key_states = {apikey.name: apikey.is_active for apikey in api_keys}

        service_dict = service.to_dict()
        service_dict["api_key_status"] = _build_api_key_status(service, api_key_states)
        service_dict["available"] = _calculate_service_availability(service, api_key_states)

        logger.info("Retrieved configuration for service: %s", service_key)
        return service_dict

    except HTTPException:
        raise
    except SQLAlchemyError as e:
        logger.error("Database error retrieving service configuration for %s: %s", service_key, e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve service configuration"
        )
    except Exception as e:
        logger.error("Unexpected error retrieving service configuration for %s: %s", service_key, e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


def get_service_categories() -> list[str]:
    """Get all available service categories."""
    try:
        categories = [category.value for category in ServiceCategory]
        logger.info("Retrieved %s service categories", len(categories))
        return categories
    except Exception as e:
        logger.error("Error retrieving service categories: %s", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve service categories"
        )


def get_service_tiers() -> list[str]:
    """Get all available service tiers."""
    try:
        tiers = [tier.value for tier in ServiceTier]
        logger.info("Retrieved %s service tiers", len(tiers))
        return tiers
    except Exception as e:
        logger.error("Error retrieving service tiers: %s", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve service tiers"
        )


def get_supported_ioc_types() -> list[str]:
    """Get all supported IOC types across all services."""
    try:
        ioc_types = set()
        for service in get_all_service_definitions().values():
            ioc_types.update(service.supported_ioc_types)
        ioc_types_list = sorted(list(ioc_types))
        logger.info("Retrieved %s supported IOC types", len(ioc_types_list))
        return ioc_types_list
    except Exception as e:
        logger.error("Error retrieving supported IOC types: %s", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve supported IOC types"
        )


async def get_services_for_ioc_type_service(db: AsyncSession, ioc_type: str) -> dict[str, dict[str, Any]]:
    """Get all services that support a specific IOC type."""
    try:
        services = get_services_for_ioc_type(ioc_type)
        if not services:
            logger.info("No services found for IOC type: %s", ioc_type)
            return {}

        api_keys = await get_apikeys(db)
        api_key_states = {apikey.name: apikey.is_active for apikey in api_keys}

        response = {}
        for key, service in services.items():
            service_dict = service.to_dict()
            service_dict["api_key_status"] = _build_api_key_status(service, api_key_states)
            service_dict["available"] = _calculate_service_availability(service, api_key_states)
            response[key] = service_dict

        logger.info("Retrieved %s services for IOC type: %s", len(response), ioc_type)
        return response

    except SQLAlchemyError as e:
        logger.error("Database error retrieving services for IOC type %s: %s", ioc_type, e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve services for IOC type"
        )
    except Exception as e:
        logger.error("Unexpected error retrieving services for IOC type %s: %s", ioc_type, e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


def _build_api_key_status(service: ServiceDefinition, api_key_states: dict[str, bool]) -> dict[str, dict[str, bool]]:
    """Build API key status information for a service."""
    return {
        required_key: {
            "configured": required_key in api_key_states,
            "active": api_key_states.get(required_key, False)
        }
        for required_key in service.required_keys
    }


def _calculate_service_availability(service: ServiceDefinition, api_key_states: dict[str, bool]) -> bool:
    """Calculate overall service availability based on required keys."""
    if not service.required_keys:
        return True
    return all(api_key_states.get(key, False) for key in service.required_keys)
