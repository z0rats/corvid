import logging

from fastapi import APIRouter, HTTPException, status

from app.features.ioc_tools.ioc_defanger.service.defang_service import batch_process_iocs
from app.features.ioc_tools.ioc_defanger.schemas.defang_schemas import (
    DefangRequest,
    DefangResponse,
    DefangErrorResponse
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/defang", tags=["IOC Defanger"])


@router.post(
    "/",
    response_model=DefangResponse,
    summary="Process IOCs for defanging or fanging",
    description="Accepts text containing IOCs and processes them according to the specified operation",
    responses={
        400: {"model": DefangErrorResponse, "description": "Invalid request"},
        422: {"model": DefangErrorResponse, "description": "Validation error"},
    }
)
async def process_iocs(request: DefangRequest) -> DefangResponse:
    logger.info("Received defang request with operation: %s", request.operation)

    try:
        result = batch_process_iocs(request.text, request.operation.value)
        logger.info("Successfully processed %s IOCs", result.total_processed)
        return result

    except ValueError as e:
        logger.warning("Validation error in defang processing: %s", str(e))
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid request: {str(e)}"
        )
