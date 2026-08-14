"""Shared upload-validation + service-dispatch skeleton for file-upload endpoints.

Extracted from `image_tools`/`email_analyzer` routers, which each duplicated the
same read-validate-then-dispatch-and-map-errors shape across every upload
endpoint. `validate_uploaded_file` covers the "read + validate" half;
`run_file_endpoint` covers the "call the service, map its errors to a 422" half
that follows.
"""

import asyncio
import logging
from collections.abc import Callable
from typing import Any

from fastapi import UploadFile, status

from app.core.exceptions import AppHTTPException, safe_error_detail

logger = logging.getLogger(__name__)


async def validate_uploaded_file(
    file: UploadFile,
    *,
    no_file_code: str,
    read_error_code: str,
    validate_fn: Callable[[str, int], tuple[bool, str | None, str | None]],
) -> bytes:
    """Read and validate an uploaded file, raising `AppHTTPException` on failure.

    `validate_fn` is a feature-specific `validate_file_upload`-shaped callable:
    `(filename, size) -> (is_valid, error_code, error_message)`.
    """
    if not file.filename:
        logger.warning("File upload rejected: no filename provided")
        raise AppHTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No file provided",
            error_code=no_file_code,
        )

    try:
        file_content = await file.read()
    except Exception as e:
        logger.error("Error reading uploaded file '%s': %s", file.filename, e)
        raise AppHTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Error reading uploaded file",
            error_code=read_error_code,
        ) from e

    is_valid, error_code, error_message = validate_fn(file.filename, len(file_content))
    if not is_valid:
        logger.warning("File upload rejected: %s", error_message)
        raise AppHTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=error_message, error_code=error_code
        )

    logger.info("File validation passed for '%s' (%s bytes)", file.filename, len(file_content))
    return file_content


async def run_file_endpoint(
    service_fn: Callable[..., Any],
    *args: Any,
    error_code: str,
    failure_message: str,
    value_error_code: str | None = None,
    run_in_thread: bool = True,
) -> Any:
    """Dispatch `service_fn(*args)` and map its errors to a 422 `AppHTTPException`.

    `run_in_thread` runs a blocking/sync `service_fn` via `asyncio.to_thread`;
    set it to `False` when `service_fn` is already a coroutine function. A
    `ValueError` maps to `value_error_code` (falls back to `error_code` when
    unset) with the exception's own message; any other exception maps to
    `error_code` with `failure_message` (or the real message outside production).
    """
    try:
        if run_in_thread:
            return await asyncio.to_thread(service_fn, *args)
        return await service_fn(*args)
    except ValueError as e:
        logger.warning("%s (validation): %s", failure_message, e)
        raise AppHTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e),
            error_code=value_error_code or error_code,
        ) from e
    except Exception as e:
        logger.error("%s: %s", failure_message, e)
        raise AppHTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=safe_error_detail(e, failure_message),
            error_code=error_code,
        ) from e
