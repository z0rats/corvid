"""Validation utilities for image tools."""

import logging

from ..config.image_config import ALLOWED_FILE_EXTENSIONS, MAX_FILE_SIZE_BYTES

logger = logging.getLogger(__name__)


def validate_file_upload(
    filename: str | None, file_size: int
) -> tuple[bool, str | None, str | None]:
    """
    Validate uploaded image file.

    Args:
        filename: Name of uploaded file
        file_size: Size of file in bytes

    Returns:
        Tuple of (is_valid, error_code, error_message). error_code is a stable
        machine-readable identifier the frontend can map to a localized message.
    """
    if not filename:
        return False, "IMAGE_NO_FILENAME", "No filename provided"

    if not any(filename.lower().endswith(ext) for ext in ALLOWED_FILE_EXTENSIONS):
        return (
            False,
            "IMAGE_INVALID_FILE_TYPE",
            f"Invalid file type. Allowed: {', '.join(ALLOWED_FILE_EXTENSIONS)}",
        )

    if file_size > MAX_FILE_SIZE_BYTES:
        return (
            False,
            "IMAGE_FILE_TOO_LARGE",
            f"File too large. Maximum size: {MAX_FILE_SIZE_BYTES // (1024 * 1024)}MB",
        )

    if file_size == 0:
        return False, "IMAGE_FILE_EMPTY", "Uploaded file is empty"

    return True, None, None
