"""
Module settings validation utilities

Pure functions for validating module settings data.
"""

from app.core.settings.modules.config.default_settings import (
    get_available_modules,
    is_valid_module_name_length,
    get_module_name_allowed_chars,
    is_available_module
)


def validate_module_name(name: str) -> bool:
    """
    Validate module name format and length
    
    Args:
        name: Module name to validate
        
    Returns:
        True if valid, False otherwise
    """
    if not name or not isinstance(name, str):
        return False
    
    # Check length constraints
    if not is_valid_module_name_length(name):
        return False
    
    # Check for valid characters
    allowed_chars = get_module_name_allowed_chars()
    return all(char in allowed_chars for char in name.strip())


def is_supported_module(name: str) -> bool:
    """
    Check if module is in the available modules list
    
    Args:
        name: Module name to check
        
    Returns:
        True if supported, False otherwise
    """
    return is_available_module(name)


def normalize_module_name(name: str) -> str | None:
    """
    Normalize module name by trimming whitespace and converting to lowercase
    
    Args:
        name: Module name to normalize
        
    Returns:
        Normalized module name or None if invalid
    """
    if not name or not isinstance(name, str):
        return None
    
    normalized = name.strip().lower()
    
    # Check if it's a valid module name after normalization
    if not normalized or not validate_module_name(normalized):
        return None
    
    return normalized


def validate_enabled_status(enabled: bool) -> bool:
    """
    Validate enabled status value
    
    Args:
        enabled: Boolean value to validate
        
    Returns:
        True if valid, False otherwise
    """
    return isinstance(enabled, bool)
