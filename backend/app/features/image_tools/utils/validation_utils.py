"""Validation utilities for image tools."""

import logging

from ..config.image_config import MAX_FILE_SIZE_BYTES, ALLOWED_FILE_EXTENSIONS

logger = logging.getLogger(__name__)


def validate_file_upload(filename: str | None, file_size: int) -> tuple[bool, str | None]:
    """
    Validate uploaded image file.

    Args:
        filename: Name of uploaded file
        file_size: Size of file in bytes

    Returns:
        Tuple of (is_valid, error_message)
    """
    if not filename:
        return False, "No filename provided"

    if not any(filename.lower().endswith(ext) for ext in ALLOWED_FILE_EXTENSIONS):
        return False, f"Invalid file type. Allowed: {', '.join(ALLOWED_FILE_EXTENSIONS)}"

    if file_size > MAX_FILE_SIZE_BYTES:
        return False, f"File too large. Maximum size: {MAX_FILE_SIZE_BYTES // (1024 * 1024)}MB"

    if file_size == 0:
        return False, "Uploaded file is empty"

    return True, None
