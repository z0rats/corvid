import json
import logging
from fastapi import APIRouter, HTTPException, Request, status
from app.core.exceptions import AppHTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from app.core.config.rate_limit_config import limiter
from app.core.dependencies import SessionDep
from app.features.ioc_tools.ioc_lookup.bulk_lookup.service.bulk_ioc_lookup_service import (
    process_bulk_lookups_with_rate_limiting
)

logger = logging.getLogger(__name__)
router = APIRouter()


class BulkLookupRequest(BaseModel):
    """Request model for bulk IOC lookups."""
    iocs: list[str]
    services: list[str]


@router.post(
    "/api/ioc-lookup/bulk",
    tags=["IOC Lookup"],
    summary="Bulk IOC lookup",
    description="Perform bulk IOC lookups across multiple services with streaming results",
    responses={400: {"description": "No IOCs or services provided"}},
)
@limiter.limit("10/minute")
async def bulk_ioc_lookup(
    request: Request,
    bulk_request: BulkLookupRequest,
    db: SessionDep,
):
    """
    Perform bulk IOC lookups across multiple services with streaming results.
    
    Args:
        request: Bulk lookup request containing IOCs and services
        db: Database session dependency
        
    Returns:
        StreamingResponse with Server-Sent Events containing results
        
    Raises:
        HTTPException: For invalid requests
    """
    logger.info("Starting bulk lookup for %s IOCs across %s services", len(bulk_request.iocs), len(bulk_request.services))
    
    if not bulk_request.iocs:
        raise AppHTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No IOCs provided", error_code="BULK_LOOKUP_NO_IOCS")

    if not bulk_request.services:
        raise AppHTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No services specified", error_code="BULK_LOOKUP_NO_SERVICES")

    async def event_stream():
        """Generate Server-Sent Events stream for bulk lookup results."""
        try:
            async for result in process_bulk_lookups_with_rate_limiting(
                bulk_request.iocs, 
                bulk_request.services, 
                db
            ):
                data = json.dumps(result)
                yield f"data: {data}\n\n"
                
        except Exception as e:
            logger.error("Error in bulk lookup stream: %s", str(e), exc_info=True)
            error_data = json.dumps({"error": "An internal error occurred during bulk lookup", "service": "system"})
            yield f"data: {error_data}\n\n"
    
    return StreamingResponse(
        event_stream(), 
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )


