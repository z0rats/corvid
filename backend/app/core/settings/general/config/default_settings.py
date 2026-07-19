"""
Default configuration for general settings

Contains default values and configuration constants for general settings.
"""

from typing import Any


# Default values for general settings
DEFAULT_GENERAL_SETTINGS: dict[str, Any] = {
    "darkmode": False,
    "language": "en"
}

# Supported UI languages
SUPPORTED_LANGUAGES = ["en", "ru"]

# Language code validation constraints
LANGUAGE_MIN_LENGTH = 2
LANGUAGE_MAX_LENGTH = 5


def get_default_darkmode() -> bool:
    """Get default darkmode setting"""
    return DEFAULT_GENERAL_SETTINGS["darkmode"]


def get_default_language() -> str:
    """Get default language setting"""
    return DEFAULT_GENERAL_SETTINGS["language"]


def get_supported_languages() -> list[str]:
    """Get list of supported language codes"""
    return SUPPORTED_LANGUAGES.copy()
