"""
General settings validation utilities

Pure functions for validating general settings data.
"""

from app.core.settings.general.config.default_settings import (
    get_supported_languages,
    get_supported_start_screens
)


def validate_language_code(language: str) -> bool:
    """
    Validate that the language code is one of the supported languages

    Args:
        language: Language code to validate

    Returns:
        True if supported, False otherwise
    """
    if not language or not isinstance(language, str):
        return False

    return language.strip().lower() in get_supported_languages()


def validate_start_screen(start_screen: str) -> bool:
    """
    Validate that the start screen is one of the supported values

    Args:
        start_screen: Start screen identifier to validate

    Returns:
        True if supported, False otherwise
    """
    if not start_screen or not isinstance(start_screen, str):
        return False

    return start_screen.strip().lower() in get_supported_start_screens()
