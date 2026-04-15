"""Validation utilities for email analyzer."""

import logging
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime

from ..config.email_config import (
    MAX_FILE_SIZE_BYTES, 
    ALLOWED_FILE_EXTENSIONS,
    MAX_EMAIL_AGE_DAYS
)

logger = logging.getLogger(__name__)


def validate_file_upload(filename: str | None, file_size: int) -> tuple[bool, str | None]:
    """
    Validate uploaded email file.
    
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
        return False, f"File too large. Maximum size: {MAX_FILE_SIZE_BYTES // (1024*1024)}MB"
    
    if file_size == 0:
        return False, "Uploaded file is empty"
    
    return True, None


def validate_email_date(date_header: str | None) -> tuple[bool, str | None]:
    """
    Validate email date header for anomalies.
    
    Args:
        date_header: Email date header value
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not date_header:
        return True, None
        
    try:
        email_date = parsedate_to_datetime(date_header)
        current_time = datetime.now(timezone.utc)
        
        if email_date > current_time:
            return False, f"Email has a future date: {date_header}"
        
        time_diff = current_time - email_date
        if time_diff.days > MAX_EMAIL_AGE_DAYS:
            return False, f"Email is {time_diff.days} days old"
            
        return True, None
        
    except Exception:
        return False, f"Email has an invalid date format: {date_header}"


def validate_hash_algorithm(hash_type: str) -> bool:
    """
    Validate if hash algorithm is supported.
    
    Args:
        hash_type: Hash algorithm name
        
    Returns:
        True if algorithm is supported
    """
    from ..config.email_config import SUPPORTED_HASH_ALGORITHMS
    return hash_type in SUPPORTED_HASH_ALGORITHMS


def sanitize_filename(filename: str) -> str:
    """
    Sanitize filename for safe processing.
    
    Args:
        filename: Original filename
        
    Returns:
        Sanitized filename
    """
    import re
    
    if not filename:
        return "unknown"
        
    sanitized = re.sub(r'[<>:"/\\|?*]', '_', filename)
    
    if len(sanitized) > 255:
        name, ext = sanitized.rsplit('.', 1) if '.' in sanitized else (sanitized, '')
        sanitized = name[:250] + ('.' + ext if ext else '')
    
    return sanitized or "unknown"
