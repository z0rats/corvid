import logging
from typing import Literal

from fastapi import APIRouter, File, Query, Request, Response, UploadFile

from app.core.config.rate_limit_config import limiter
from app.core.dependencies import ReadSessionDep
from app.core.utils.file_upload import run_file_endpoint, validate_uploaded_file

from ..config.image_config import ALLOWED_FILE_EXTENSIONS, MAX_FILE_SIZE_BYTES
from ..schemas.image_schemas import (
    ChronoverifyResponse,
    ImageAnalysisResponse,
    ImageAnomalyResponse,
    ImageCompareResponse,
    ImageGeolocationResponse,
    ImageHealthResponse,
    ImageStructureResponse,
    ImageVisualAnalysisResponse,
    StreetViewKeyResponse,
)
from ..service.chronoverify_service import check_image_provenance
from ..service.exiftool_service import get_exiftool_version
from ..service.google_maps_service import get_google_maps_key
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


async def _validate_uploaded_image(file: UploadFile) -> bytes:
    return await validate_uploaded_file(
        file,
        no_file_code="IMAGE_NO_FILE",
        read_error_code="IMAGE_READ_ERROR",
        validate_fn=validate_file_upload,
    )


@router.post(
    "/analyze",
    response_model=ImageAnalysisResponse,
    response_model_exclude_none=True,
    summary="Analyze image file for metadata",
    description=(
        "Upload an image file to extract EXIF/GPS metadata, file properties, and hash values."
    ),
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

    file_content = await _validate_uploaded_image(file)

    result = await run_file_endpoint(
        analyze_image_content,
        file.filename,
        file_content,
        error_code="IMAGE_ANALYSIS_FAILED",
        failure_message="Image analysis failed",
    )

    if result.gps:
        result.gps.address = await reverse_geocode(result.gps.latitude, result.gps.longitude)

    logger.info("Image analysis completed successfully for '%s'", file.filename)
    return result


@router.post(
    "/geolocate",
    response_model=ImageGeolocationResponse,
    summary="Analyze image for AI-based location clues",
    description="Upload an image file to get an AI-generated location hypothesis based on visual "
    "clues (signage, architecture, vegetation, road markings, etc.), with reasoning per clue.",
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

    file_content = await _validate_uploaded_image(file)

    result = await run_file_endpoint(
        analyze_image_location,
        file.filename,
        file_content,
        db,
        error_code="IMAGE_GEOLOCATION_FAILED",
        failure_message="Image geolocation failed",
        run_in_thread=False,
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

    file_content = await _validate_uploaded_image(file)

    result = await run_file_endpoint(
        analyze_jpeg_structure,
        file.filename,
        file_content,
        error_code="IMAGE_STRUCTURE_FAILED",
        failure_message="Structure analysis failed",
        value_error_code="IMAGE_NOT_JPEG",
    )

    logger.info("Structure analysis completed successfully for '%s'", file.filename)
    return result


@router.post(
    "/anomalies",
    response_model=ImageAnomalyResponse,
    summary="Run tamper/anomaly heuristics on an image",
    description="Upload an image to check EXIF timestamp consistency, editing-software "
    "fingerprints, embedded thumbnail vs main image mismatch, trailing data after EOI, marker "
    "order, and quantization table consistency (JPEG-only checks are skipped for other formats).",
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

    file_content = await _validate_uploaded_image(file)

    result = await run_file_endpoint(
        analyze_image_anomalies,
        file.filename,
        file_content,
        error_code="IMAGE_ANOMALY_DETECTION_FAILED",
        failure_message="Anomaly detection failed",
    )

    logger.info(
        "Anomaly detection completed successfully for '%s' - %s findings",
        file.filename,
        len(result.findings),
    )
    return result


@router.post(
    "/chronoverify",
    response_model=ChronoverifyResponse,
    summary="Check image provenance and manipulation signals via ChronoVerify",
    description="Upload an image to ChronoVerify (https://chronoverify.com) for a "
    "capture-time/C2PA-provenance and pixel-forensics verdict. Sends the image to a "
    "third-party service - opt-in only, unlike this module's other (local) checks. "
    "Works keyless (free, rate-limited); an optional API key under Settings > API "
    "Keys raises the limit.",
    responses={
        400: {"description": "Invalid or missing file"},
        422: {"description": "Provenance check failed, or ChronoVerify rejected the file"},
    },
)
@limiter.limit("10/minute")
async def check_image_provenance_route(
    request: Request,
    db: ReadSessionDep,
    file: UploadFile = File(..., description="Image file to check"),
) -> ChronoverifyResponse:
    logger.info("Received ChronoVerify provenance check request for file: %s", file.filename)

    file_content = await _validate_uploaded_image(file)

    result = await run_file_endpoint(
        check_image_provenance,
        file.filename,
        file_content,
        db,
        error_code="IMAGE_CHRONOVERIFY_FAILED",
        failure_message="Provenance check failed",
        value_error_code="IMAGE_CHRONOVERIFY_REJECTED",
        run_in_thread=False,
    )

    logger.info(
        "ChronoVerify check completed for '%s' - verdict: %s", file.filename, result.verdict
    )
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

    file_content = await _validate_uploaded_image(file)

    result = await run_file_endpoint(
        analyze_image_visuals,
        file.filename,
        file_content,
        error_code="IMAGE_VISUAL_ANALYSIS_FAILED",
        failure_message="Visual analysis failed",
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
    logger.info(
        "Received image comparison request for files: %s, %s",
        file_left.filename,
        file_right.filename,
    )

    left_content = await _validate_uploaded_image(file_left)
    right_content = await _validate_uploaded_image(file_right)

    result = await run_file_endpoint(
        compare_images,
        file_left.filename,
        left_content,
        file_right.filename,
        right_content,
        error_code="IMAGE_COMPARE_FAILED",
        failure_message="Image comparison failed",
    )

    logger.info(
        "Image comparison completed successfully for '%s'/'%s'",
        file_left.filename,
        file_right.filename,
    )
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
    mode: Literal["all", "location_only"] = Query(
        "all", description="'all' strips every metadata field, 'location_only' strips just GPS"
    ),
) -> Response:
    logger.info("Received metadata removal request for file: %s (mode=%s)", file.filename, mode)

    file_content = await _validate_uploaded_image(file)

    cleaned_bytes, media_type, out_filename = await run_file_endpoint(
        strip_metadata,
        file.filename,
        file_content,
        mode,
        error_code="IMAGE_STRIP_FAILED",
        failure_message="Metadata removal failed",
    )

    logger.info("Metadata removal completed successfully for '%s'", file.filename)
    return Response(
        content=cleaned_bytes,
        media_type=media_type,
        headers={"Content-Disposition": f'attachment; filename="{out_filename}"'},
    )


@router.get(
    "/street-view-key",
    response_model=StreetViewKeyResponse,
    summary="Get the configured Google Maps key for the client-side Street View embed",
    description=(
        "Returns the raw Google Maps key if one is configured and active, or null "
        "otherwise. Unlike other API keys in this app, this one is meant to be read "
        "directly by the browser (Google's Maps Embed API), not proxied server-side."
    ),
)
async def get_street_view_key(db: ReadSessionDep) -> StreetViewKeyResponse:
    return StreetViewKeyResponse(key=await get_google_maps_key(db))


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
            "/api/image/chronoverify",
            "/api/image/visual-analysis",
            "/api/image/compare",
            "/api/image/strip-metadata",
            "/api/image/health",
        ],
        supported_formats=ALLOWED_FILE_EXTENSIONS,
        max_file_size=f"{MAX_FILE_SIZE_BYTES // (1024 * 1024)}MB",
        exiftool_version=get_exiftool_version(),
    )
