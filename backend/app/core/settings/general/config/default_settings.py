"""
Default configuration for general settings

Contains default values and configuration constants for general settings.
"""

from typing import Any


# Default values for general settings
DEFAULT_GENERAL_SETTINGS: dict[str, Any] = {
    "darkmode": False,
    "font": "Poppins"
}

# Supported font families
SUPPORTED_FONTS = [
    "Poppins",
    "Arial", 
    "Helvetica",
    "Times New Roman",
    "Georgia",
    "Verdana",
    "Trebuchet MS",
    "Courier New",
    "Lucida Console",
    "Monaco"
]

# Font validation constraints
FONT_MIN_LENGTH = 1
FONT_MAX_LENGTH = 50

# Allowed characters in font names
FONT_ALLOWED_CHARS = set("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789 -")


def get_default_darkmode() -> bool:
    """Get default darkmode setting"""
    return DEFAULT_GENERAL_SETTINGS["darkmode"]


def get_default_font() -> str:
    """Get default font setting"""
    return DEFAULT_GENERAL_SETTINGS["font"]


def get_supported_fonts() -> list[str]:
    """Get list of supported fonts"""
    return SUPPORTED_FONTS.copy()


def is_valid_font_length(font: str) -> bool:
    """Check if font name length is valid"""
    return FONT_MIN_LENGTH <= len(font.strip()) <= FONT_MAX_LENGTH


def get_font_allowed_chars() -> set[str]:
    """Get set of allowed characters for font names"""
    return FONT_ALLOWED_CHARS.copy()
