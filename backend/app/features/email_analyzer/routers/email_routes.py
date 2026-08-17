import logging
from typing import Literal

from fastapi import APIRouter, File, Request, Response, UploadFile, status
from pydantic import BaseModel, Field

from app.core.config.rate_limit_config import limiter
from app.core.dependencies import ReadSessionDep
from app.core.exceptions import AppHTTPException
from app.core.utils.file_upload import run_file_endpoint, validate_uploaded_file

from ..config.email_config import ALLOWED_FILE_EXTENSIONS, MAX_FILE_SIZE_BYTES
from ..schemas.email_schemas import EmailAnalysisResponse, EmailHealthResponse
from ..service.email_ai_analysis_service import analyze_email_body
from ..service.email_analyzer_service import analyze_email_content
from ..service.report_service import generate_analysis_report
from ..utils.validation_utils import validate_file_upload

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/email", tags=["Email Analyzer"])


async def _validate_uploaded_email(file: UploadFile) -> bytes:
    return await validate_uploaded_file(
        file,
        no_file_code="EMAIL_NO_FILE",
        read_error_code="EMAIL_FILE_READ_ERROR",
        validate_fn=validate_file_upload,
    )


@router.post(
    "/analyze",
    response_model=EmailAnalysisResponse,
    response_model_exclude_none=True,
    summary="Analyze email file for security threats",
    description=(
        "Upload an .eml file for comprehensive security analysis including "
        "header validation, attachment scanning, and threat detection."
    ),
    responses={
        400: {"description": "Invalid or missing file"},
        422: {"description": "Email analysis failed"},
    },
)
@limiter.limit("20/minute")
async def analyze_email_file(
    request: Request,
    file: UploadFile = File(
        ..., description="Email file to analyze (.eml format)", media_type="message/rfc822"
    ),
) -> EmailAnalysisResponse:
    logger.info("Received email analysis request for file: %s", file.filename)

    file_content = await _validate_uploaded_email(file)

    result = await run_file_endpoint(
        analyze_email_content,
        file_content,
        error_code="EMAIL_ANALYSIS_FAILED",
        failure_message="Email analysis failed",
    )

    logger.info("Email analysis completed successfully for '%s'", file.filename)
    return result


class EmailAiAnalysisRequest(BaseModel):
    input: str = Field(
        ..., min_length=1, max_length=500000, description="Email message body text to analyze"
    )


@router.post(
    "/ai-analysis",
    summary="Analyze email body with AI",
    description=(
        "Use an LLM to analyze the email message body for phishing, social "
        "engineering, and other security threats."
    ),
)
@limiter.limit("10/minute")
async def ai_analyze_email_body(
    request: Request,
    body: EmailAiAnalysisRequest,
    db: ReadSessionDep,
) -> dict:
    logger.info("Received AI email body analysis request (%d chars)", len(body.input))

    try:
        result = await analyze_email_body(email_body=body.input, db=db)
    except ValueError as e:
        logger.error("AI email analysis failed: %s", e)
        raise AppHTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e),
            error_code="EMAIL_AI_ANALYSIS_FAILED",
        ) from e

    return {"analysis_result": result}


@router.post(
    "/report",
    summary="Export an email analysis result as a report",
    description=(
        "Render a previously computed analysis result (as returned by /analyze) "
        "as an HTML or PDF report"
    ),
)
async def export_analysis_report(
    result: EmailAnalysisResponse,
    format: Literal["html", "pdf"] = "html",
    locale: Literal["en", "ru"] = "en",
) -> Response:
    content, media_type, filename = generate_analysis_report(result, format, locale)
    return Response(
        content=content,
        media_type=media_type,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get(
    "/health",
    response_model=EmailHealthResponse,
    summary="Email analyzer health check",
    description="Check the health status of the email analyzer service.",
)
async def health_check() -> EmailHealthResponse:
    return EmailHealthResponse(
        service="email_analyzer",
        status="healthy",
        endpoints=["/api/email/analyze", "/api/email/report", "/api/email/health"],
        supported_formats=ALLOWED_FILE_EXTENSIONS,
        max_file_size=f"{MAX_FILE_SIZE_BYTES // (1024 * 1024)}MB",
    )
