import asyncio
import logging
from typing import Literal

from fastapi import APIRouter, File, HTTPException, Query, Request, Response, UploadFile, status

from app.core.config.rate_limit_config import limiter
from app.core.dependencies import ReadSessionDep
from app.core.exceptions import AppHTTPException, safe_error_detail
from ..config.image_config import ALLOWED_FILE_EXTENSIONS, MAX_FILE_SIZE_BYTES
from ..schemas.image_schemas import (
    ImageAnalysisResponse,
    ImageAnomalyResponse,
    ImageCompareResponse,
    ImageGeolocationResponse,
    ImageHealthResponse,
    ImageStructureResponse,
    ImageVisualAnalysisResponse,
)
from ..service.image_anomaly_service import analyze_image_anomalies
from ..service.image_compare_service import compare_images
from ..service.image_geolocation_service import analyze_image_location
from ..service.image_metadata_removal_service import strip_metadata
from ..service.image_metadata_service import analyze_image_content
from ..service.image_structure_service import analyze_jpeg_structure
from ..service.image_visual_analysis_service import analyze_image_visuals
from ..service.reverse_geocode_service import reverse_geocode
from ..utils.validation_utils import validate_file_upload

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/image", tags=["Image Tools"])


async def validate_uploaded_file(file: UploadFile) -> bytes:
    """Validate and read the uploaded image file, raising HTTPException on failure."""
    if not file.filename:
        logger.warning("File upload rejected: no filename provided")
        raise AppHTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No file provided", error_code="IMAGE_NO_FILE")

    try:
        file_content = await file.read()
    except Exception as e:
        logger.error("Error reading uploaded file '%s': %s", file.filename, e)
        raise AppHTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Error reading uploaded file", error_code="IMAGE_READ_ERROR")

    is_valid, error_message = validate_file_upload(file.filename, len(file_content))
    if not is_valid:
        logger.warning("File upload rejected: %s", error_message)
        raise AppHTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=error_message, error_code="IMAGE_VALIDATION_ERROR")

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
        raise AppHTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=safe_error_detail(e, "Image analysis failed"),
            error_code="IMAGE_ANALYSIS_FAILED",
        )

    if result.gps:
        result.gps.address = await reverse_geocode(result.gps.latitude, result.gps.longitude)

    logger.info("Image analysis completed successfully for '%s'", file.filename)
    return result


@router.post(
    "/geolocate",
    response_model=ImageGeolocationResponse,
    summary="Analyze image for AI-based location clues",
    description="Upload an image file to get an AI-generated location hypothesis based on visual clues "
                "(signage, architecture, vegetation, road markings, etc.), with reasoning per clue.",
    responses={
        400: {"description": "Invalid or missing file"},
        422: {"description": "Geolocation analysis failed"},
    },
)
@limiter.limit("10/minute")
async def geolocate_image_file(
    request: Request,
    db: ReadSessionDep,
    file: UploadFile = File(..., description="Image file to analyze"),
) -> ImageGeolocationResponse:
    logger.info("Received image geolocation request for file: %s", file.filename)

    file_content = await validate_uploaded_file(file)

    try:
        result = await analyze_image_location(filename=file.filename, image_data=file_content, db=db)
    except ValueError as e:
        logger.error("Image geolocation failed for '%s': %s", file.filename, e)
        raise AppHTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e),
            error_code="IMAGE_GEOLOCATION_FAILED",
        )
    except Exception as e:
        logger.error("Image geolocation failed for '%s': %s", file.filename, e)
        raise AppHTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=safe_error_detail(e, "Image geolocation failed"),
            error_code="IMAGE_GEOLOCATION_FAILED",
        )

    logger.info("Image geolocation completed successfully for '%s'", file.filename)
    return result


@router.post(
    "/structure",
    response_model=ImageStructureResponse,
    response_model_exclude_none=True,
    summary="Analyze JPEG structure",
    description="Upload a JPEG to inspect its marker map, quantization/Huffman tables, "
                "frame parameters, and an estimated save quality.",
    responses={
        400: {"description": "Invalid or missing file"},
        422: {"description": "Structure analysis failed, or file is not a JPEG"},
    },
)
@limiter.limit("20/minute")
async def analyze_image_structure(
    request: Request,
    file: UploadFile = File(..., description="JPEG file to analyze"),
) -> ImageStructureResponse:
    logger.info("Received image structure analysis request for file: %s", file.filename)

    file_content = await validate_uploaded_file(file)

    try:
        result = await asyncio.to_thread(analyze_jpeg_structure, file.filename, file_content)
    except ValueError as e:
        logger.warning("Structure analysis rejected for '%s': %s", file.filename, e)
        raise AppHTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e),
            error_code="IMAGE_NOT_JPEG",
        )
    except Exception as e:
        logger.error("Structure analysis failed for '%s': %s", file.filename, e)
        raise AppHTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=safe_error_detail(e, "Structure analysis failed"),
            error_code="IMAGE_STRUCTURE_FAILED",
        )

    logger.info("Structure analysis completed successfully for '%s'", file.filename)
    return result


@router.post(
    "/anomalies",
    response_model=ImageAnomalyResponse,
    summary="Run tamper/anomaly heuristics on an image",
    description="Upload an image to check EXIF timestamp consistency, editing-software fingerprints, "
                "embedded thumbnail vs main image mismatch, trailing data after EOI, marker order, "
                "and quantization table consistency (JPEG-only checks are skipped for other formats).",
    responses={
        400: {"description": "Invalid or missing file"},
        422: {"description": "Anomaly detection failed"},
    },
)
@limiter.limit("20/minute")
async def analyze_image_anomalies_route(
    request: Request,
    file: UploadFile = File(..., description="Image file to check"),
) -> ImageAnomalyResponse:
    logger.info("Received image anomaly detection request for file: %s", file.filename)

    file_content = await validate_uploaded_file(file)

    try:
        result = await asyncio.to_thread(analyze_image_anomalies, file.filename, file_content)
    except ValueError as e:
        logger.warning("Anomaly detection rejected for '%s': %s", file.filename, e)
        raise AppHTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e),
            error_code="IMAGE_ANOMALY_DETECTION_FAILED",
        )
    except Exception as e:
        logger.error("Anomaly detection failed for '%s': %s", file.filename, e)
        raise AppHTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=safe_error_detail(e, "Anomaly detection failed"),
            error_code="IMAGE_ANOMALY_DETECTION_FAILED",
        )

    logger.info("Anomaly detection completed successfully for '%s' - %s findings", file.filename, len(result.findings))
    return result


@router.post(
    "/visual-analysis",
    response_model=ImageVisualAnalysisResponse,
    summary="Pixel-level visual analysis",
    description="Upload an image to get RGB/luminance/chroma histograms and a CbCr vectorscope.",
    responses={
        400: {"description": "Invalid or missing file"},
        422: {"description": "Visual analysis failed"},
    },
)
@limiter.limit("20/minute")
async def analyze_image_visuals_route(
    request: Request,
    file: UploadFile = File(..., description="Image file to analyze"),
) -> ImageVisualAnalysisResponse:
    logger.info("Received image visual analysis request for file: %s", file.filename)

    file_content = await validate_uploaded_file(file)

    try:
        result = await asyncio.to_thread(analyze_image_visuals, file.filename, file_content)
    except ValueError as e:
        logger.warning("Visual analysis rejected for '%s': %s", file.filename, e)
        raise AppHTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e),
            error_code="IMAGE_VISUAL_ANALYSIS_FAILED",
        )
    except Exception as e:
        logger.error("Visual analysis failed for '%s': %s", file.filename, e)
        raise AppHTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=safe_error_detail(e, "Visual analysis failed"),
            error_code="IMAGE_VISUAL_ANALYSIS_FAILED",
        )

    logger.info("Visual analysis completed successfully for '%s'", file.filename)
    return result


@router.post(
    "/compare",
    response_model=ImageCompareResponse,
    summary="Compare two images field by field",
    description="Upload two images to diff their EXIF/IPTC/XMP fields and compare pixel "
                "content via a perceptual-hash distance.",
    responses={
        400: {"description": "Invalid or missing file"},
        422: {"description": "Comparison failed"},
    },
)
@limiter.limit("10/minute")
async def compare_image_files(
    request: Request,
    file_left: UploadFile = File(..., description="First image to compare"),
    file_right: UploadFile = File(..., description="Second image to compare"),
) -> ImageCompareResponse:
    logger.info("Received image comparison request for files: %s, %s", file_left.filename, file_right.filename)

    left_content = await validate_uploaded_file(file_left)
    right_content = await validate_uploaded_file(file_right)

    try:
        result = await asyncio.to_thread(
            compare_images, file_left.filename, left_content, file_right.filename, right_content
        )
    except Exception as e:
        logger.error("Image comparison failed for '%s'/'%s': %s", file_left.filename, file_right.filename, e)
        raise AppHTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=safe_error_detail(e, "Image comparison failed"),
            error_code="IMAGE_COMPARE_FAILED",
        )

    logger.info("Image comparison completed successfully for '%s'/'%s'", file_left.filename, file_right.filename)
    return result


@router.post(
    "/strip-metadata",
    summary="Remove metadata from an image",
    description="Upload an image and download a copy with metadata removed. JPEGs are "
                "cleaned losslessly at the byte level; other formats use a best-effort re-encode.",
    responses={
        400: {"description": "Invalid or missing file"},
        422: {"description": "Metadata removal failed"},
    },
)
@limiter.limit("15/minute")
async def strip_image_metadata(
    request: Request,
    file: UploadFile = File(..., description="Image file to clean"),
    mode: Literal["all", "location_only"] = Query("all", description="'all' strips every metadata field, 'location_only' strips just GPS"),
) -> Response:
    logger.info("Received metadata removal request for file: %s (mode=%s)", file.filename, mode)

    file_content = await validate_uploaded_file(file)

    try:
        cleaned_bytes, media_type, out_filename = await asyncio.to_thread(strip_metadata, file.filename, file_content, mode)
    except ValueError as e:
        logger.warning("Metadata removal rejected for '%s': %s", file.filename, e)
        raise AppHTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e),
            error_code="IMAGE_STRIP_FAILED",
        )
    except Exception as e:
        logger.error("Metadata removal failed for '%s': %s", file.filename, e)
        raise AppHTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=safe_error_detail(e, "Metadata removal failed"),
            error_code="IMAGE_STRIP_FAILED",
        )

    logger.info("Metadata removal completed successfully for '%s'", file.filename)
    return Response(
        content=cleaned_bytes,
        media_type=media_type,
        headers={"Content-Disposition": f'attachment; filename="{out_filename}"'},
    )


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
        endpoints=[
            "/api/image/analyze",
            "/api/image/geolocate",
            "/api/image/structure",
            "/api/image/anomalies",
            "/api/image/visual-analysis",
            "/api/image/compare",
            "/api/image/strip-metadata",
            "/api/image/health",
        ],
        supported_formats=ALLOWED_FILE_EXTENSIONS,
        max_file_size=f"{MAX_FILE_SIZE_BYTES // (1024 * 1024)}MB",
    )
