"""Domain lookup API routes"""

import logging
from typing import Any

from fastapi import APIRouter, Request, status

from app.core.config.rate_limit_config import limiter
from app.features.ioc_tools.domain_finder.schemas.domain_schemas import (
    DomainLookupRequest,
    DomainLookupResponse,
)
from app.features.ioc_tools.domain_finder.service.domain_lookup_service import perform_domain_lookup

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/domain", tags=["Domain Lookup"])


@router.post(
    "/lookup",
    response_model=DomainLookupResponse,
    status_code=status.HTTP_200_OK,
    summary="Perform domain lookup using URLScan.io",
    description="Lookup domain information using the URLScan.io API to find scan results and security information"
)
@limiter.limit("30/minute")
async def lookup_domain_post(request: Request, domain_request: DomainLookupRequest) -> DomainLookupResponse:
    """Perform comprehensive domain lookup using URLScan.io API via POST request"""
    logger.info("POST domain lookup request - Domain: %s", domain_request.domain)
    result = await perform_domain_lookup(domain_request)
    logger.info("POST domain lookup completed - Domain: %s, Results: %s", domain_request.domain, result.total_results)
    return result


@router.get(
    "/lookup/{domain}",
    response_model=DomainLookupResponse,
    status_code=status.HTTP_200_OK,
    summary="Perform domain lookup via URL parameter",
    description="Lookup domain information using URL parameter for simple GET requests"
)
@limiter.limit("30/minute")
async def lookup_domain_get(request: Request, domain: str) -> DomainLookupResponse:
    """Perform domain lookup using domain from URL path via GET request"""
    logger.info("GET domain lookup request - Domain: %s", domain)
    domain_request = DomainLookupRequest(domain=domain)
    result = await perform_domain_lookup(domain_request)
    logger.info("GET domain lookup completed - Domain: %s, Results: %s", domain, result.total_results)
    return result


@router.get(
    "/health",
    response_model=dict[str, Any],
    status_code=status.HTTP_200_OK,
    summary="Check domain lookup service health",
    description="Health check endpoint for the domain lookup service"
)
async def check_domain_service_health() -> dict[str, Any]:
    """Check if the domain lookup service is operational"""
    return {
        "service": "domain_lookup",
        "status": "healthy",
        "endpoints": [
            "/api/domain/lookup",
            "/api/domain/lookup/{domain}"
        ]
    }
