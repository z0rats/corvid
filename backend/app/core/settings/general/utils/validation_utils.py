"""
General settings validation utilities

Pure functions for validating general settings data.
"""

from app.core.settings.general.config.default_settings import (
    get_supported_fonts,
    is_valid_font_length,
    get_font_allowed_chars,
    get_default_font
)


def validate_font_name(font: str) -> bool:
    """
    Validate font name format and length
    
    Args:
        font: Font name to validate
        
    Returns:
        True if valid, False otherwise
    """
    if not font or not isinstance(font, str):
        return False
    
    # Check length constraints
    if not is_valid_font_length(font):
        return False
    
    # Check for valid characters
    allowed_chars = get_font_allowed_chars()
    return all(char in allowed_chars for char in font.strip())


def is_supported_font(font: str) -> bool:
    """
    Check if font is in the supported fonts list
    
    Args:
        font: Font name to check
        
    Returns:
        True if supported, False otherwise
    """
    return font in get_supported_fonts()


def normalize_font_name(font: str) -> str:
    """
    Normalize font name by trimming whitespace and capitalizing properly
    
    Args:
        font: Font name to normalize
        
    Returns:
        Normalized font name
    """
    if not font or not isinstance(font, str):
        return get_default_font()
    
    normalized = font.strip()
    
    # If it's a supported font, return the canonical version
    supported_fonts = get_supported_fonts()
    for supported_font in supported_fonts:
        if normalized.lower() == supported_font.lower():
            return supported_font
    
    # Otherwise return the trimmed version
    return normalized if normalized else get_default_font()
