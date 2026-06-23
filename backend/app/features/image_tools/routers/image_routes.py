import asyncio
import logging

from fastapi import APIRouter, File, HTTPException, Request, UploadFile, status

from app.core.config.rate_limit_config import limiter
from app.core.exceptions import safe_error_detail
from ..config.image_config import ALLOWED_FILE_EXTENSIONS, MAX_FILE_SIZE_BYTES
from ..schemas.image_schemas import ImageAnalysisResponse, ImageHealthResponse
from ..service.image_metadata_service import analyze_image_content
from ..utils.validation_utils import validate_file_upload

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/image", tags=["Image Tools"])


async def validate_uploaded_file(file: UploadFile) -> bytes:
    """Validate and read the uploaded image file, raising HTTPException on failure."""
    if not file.filename:
        logger.warning("File upload rejected: no filename provided")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No file provided")

    try:
        file_content = await file.read()
    except Exception as e:
        logger.error("Error reading uploaded file '%s': %s", file.filename, e)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Error reading uploaded file")

    is_valid, error_message = validate_file_upload(file.filename, len(file_content))
    if not is_valid:
        logger.warning("File upload rejected: %s", error_message)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=error_message)

    logger.info("File validation passed for '%s' (%s bytes)", file.filename, len(file_content))
    return file_content


@router.post(
    "/analyze",
    response_model=ImageAnalysisResponse,
    response_model_exclude_none=True,
    summary="Analyze image file for metadata",
    description="Upload an image file to extract EXIF/GPS metadata, file properties, and hash values.",
    responses={
        400: {"description": "Invalid or missing file"},
        422: {"description": "Image analysis failed"},
    },
)
@limiter.limit("20/minute")
async def analyze_image_file(
    request: Request,
    file: UploadFile = File(..., description="Image file to analyze"),
) -> ImageAnalysisResponse:
    logger.info("Received image analysis request for file: %s", file.filename)

    file_content = await validate_uploaded_file(file)

    try:
        result = await asyncio.to_thread(analyze_image_content, file.filename, file_content)
    except Exception as e:
        logger.error("Image analysis failed for '%s': %s", file.filename, e)
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=safe_error_detail(e, "Image analysis failed"),
        )

    logger.info("Image analysis completed successfully for '%s'", file.filename)
    return result


@router.get(
    "/health",
    response_model=ImageHealthResponse,
    summary="Image tools health check",
    description="Check the health status of the image tools service.",
)
async def health_check() -> ImageHealthResponse:
    return ImageHealthResponse(
        service="image_tools",
        status="healthy",
        endpoints=["/api/image/analyze", "/api/image/health"],
        supported_formats=ALLOWED_FILE_EXTENSIONS,
        max_file_size=f"{MAX_FILE_SIZE_BYTES // (1024 * 1024)}MB",
    )
