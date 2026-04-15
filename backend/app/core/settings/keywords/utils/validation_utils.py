"""
Validation utilities for keywords settings

Contains validation functions and utilities for keyword processing.
"""

import re




# Keyword validation constraints
KEYWORD_MIN_LENGTH = 1
KEYWORD_MAX_LENGTH = 100

# Allowed characters in keywords (alphanumeric, spaces, hyphens, underscores)
KEYWORD_ALLOWED_CHARS = set("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789 -_")

# Regex pattern for valid keywords
KEYWORD_PATTERN = re.compile(r'^[a-zA-Z0-9\s\-_]+$')


def validate_keyword_format(keyword: str) -> bool:
    """
    Validate keyword format and constraints
    
    Args:
        keyword: The keyword string to validate
        
    Returns:
        bool: True if keyword is valid, False otherwise
    """
    if not keyword or not isinstance(keyword, str):
        return False
    
    # Check length constraints
    if not is_valid_keyword_length(keyword):
        return False
    
    # Check allowed characters
    if not has_valid_keyword_chars(keyword):
        return False
    
    # Check pattern match
    if not KEYWORD_PATTERN.match(keyword.strip()):
        return False
    
    # Check for empty or whitespace-only keywords
    if not keyword.strip():
        return False
    
    return True


def normalize_keyword(keyword: str) -> str:
    """
    Normalize keyword by trimming whitespace and converting to lowercase
    
    Args:
        keyword: The keyword string to normalize
        
    Returns:
        str: Normalized keyword
    """
    if not keyword:
        return ""
    
    # Strip whitespace and convert to lowercase
    normalized = keyword.strip().lower()
    
    # Replace multiple spaces with single space
    normalized = re.sub(r'\s+', ' ', normalized)
    
    return normalized


def is_valid_keyword_length(keyword: str) -> bool:
    """
    Check if keyword length is within valid range
    
    Args:
        keyword: The keyword string to check
        
    Returns:
        bool: True if length is valid, False otherwise
    """
    if not keyword:
        return False
    
    trimmed_length = len(keyword.strip())
    return KEYWORD_MIN_LENGTH <= trimmed_length <= KEYWORD_MAX_LENGTH


def has_valid_keyword_chars(keyword: str) -> bool:
    """
    Check if keyword contains only allowed characters
    
    Args:
        keyword: The keyword string to check
        
    Returns:
        bool: True if all characters are allowed, False otherwise
    """
    if not keyword:
        return False
    
    return all(char in KEYWORD_ALLOWED_CHARS for char in keyword)


def get_keyword_allowed_chars() -> set[str]:
    """
    Get set of allowed characters for keywords
    
    Returns:
        set[str]: Set of allowed characters
    """
    return KEYWORD_ALLOWED_CHARS.copy()


def get_keyword_constraints() -> dict:
    """
    Get keyword validation constraints
    
    Returns:
        dict: Dictionary containing validation constraints
    """
    return {
        "min_length": KEYWORD_MIN_LENGTH,
        "max_length": KEYWORD_MAX_LENGTH,
        "allowed_chars": list(KEYWORD_ALLOWED_CHARS),
        "pattern": KEYWORD_PATTERN.pattern
    }


def sanitize_keyword(keyword: str) -> str:
    """
    Sanitize keyword by removing invalid characters
    
    Args:
        keyword: The keyword string to sanitize
        
    Returns:
        str: Sanitized keyword
    """
    if not keyword:
        return ""
    
    # Remove invalid characters
    sanitized = ''.join(char for char in keyword if char in KEYWORD_ALLOWED_CHARS)
    
    # Normalize the result
    return normalize_keyword(sanitized)
