import logging

from fastapi import FastAPI, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.requests import Request

from app.core.config.settings import settings

logger = logging.getLogger(__name__)


class ApplicationError(Exception):
    """Exception for intentional business logic errors.

    Raise this in service/route code instead of bare ValueError or HTTPException
    so that errors are logged and return a consistent JSON response.
    The registered handler logs the error and maps it to the given status code.
    """

    def __init__(self, message: str, status_code: int = 400) -> None:
        if not (400 <= status_code <= 599):
            raise ValueError(f"ApplicationError status_code must be 4xx or 5xx, got {status_code}")
        self.status_code = status_code
        self.detail = message
        super().__init__(message)


def _sanitize_validation_errors(errors: list[dict]) -> list[dict]:
    """Strip internal details from validation errors in production.

    Pydantic v2 errors include a 'url' field linking to docs and full
    field paths in 'loc'. In production, only msg/type are returned
    to avoid exposing internal schema details to clients.
    """
    if settings.environment != "production":
        return errors

    return [
        {
            "msg": err.get("msg", ""),
            "type": err.get("type", ""),
        }
        for err in errors
    ]


async def http_exception_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
    """Handle HTTP exceptions with consistent JSON format"""
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail},
    )


async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    """Handle request validation errors with structured detail"""
    logger.warning("Validation error on %s %s: %s", request.method, request.url.path, exc.errors())
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "detail": "Validation error",
            "errors": _sanitize_validation_errors(exc.errors()),
        },
    )


async def application_error_handler(request: Request, exc: ApplicationError) -> JSONResponse:
    """Handle intentional business logic errors"""
    logger.warning("Application error on %s %s: %s", request.method, request.url.path, exc.detail)
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail},
    )


async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Handle unexpected exceptions with logging"""
    logger.error("Unhandled exception on %s %s: %s", request.method, request.url.path, exc, exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "Internal server error"},
    )


def safe_error_detail(exc: Exception, fallback: str = "An unexpected error occurred") -> str:
    """Return the exception message in development, a generic fallback in production.

    Use this when converting caught exceptions into HTTPException details
    so that internal error details are never leaked to clients in production.
    """
    if settings.environment != "production":
        return str(exc)
    return fallback


def register_exception_handlers(app: FastAPI) -> None:
    """Register all global exception handlers on the FastAPI application"""
    app.add_exception_handler(StarletteHTTPException, http_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(ApplicationError, application_error_handler)
    app.add_exception_handler(Exception, generic_exception_handler)
