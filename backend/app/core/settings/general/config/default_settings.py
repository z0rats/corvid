"""
Default configuration for general settings

Contains default values and configuration constants for general settings.
"""

from typing import Any


# Default values for general settings
DEFAULT_GENERAL_SETTINGS: dict[str, Any] = {
    "darkmode": False,
    "language": "en",
    "auto_open_on_single_match": True,
    "start_screen": "search",
    "always_tiles": False,
}

# Supported UI languages
SUPPORTED_LANGUAGES = ["en", "ru"]

# Language code validation constraints
LANGUAGE_MIN_LENGTH = 2
LANGUAGE_MAX_LENGTH = 5

# Command palette start-screen options
SUPPORTED_START_SCREENS = ["search", "newsfeed"]

# start_screen column validation constraints
START_SCREEN_MIN_LENGTH = 2
START_SCREEN_MAX_LENGTH = 20


def get_default_darkmode() -> bool:
    """Get default darkmode setting"""
    return DEFAULT_GENERAL_SETTINGS["darkmode"]


def get_default_language() -> str:
    """Get default language setting"""
    return DEFAULT_GENERAL_SETTINGS["language"]


def get_supported_languages() -> list[str]:
    """Get list of supported language codes"""
    return SUPPORTED_LANGUAGES.copy()


def get_default_auto_open_on_single_match() -> bool:
    """Get default auto-open-on-single-match setting"""
    return DEFAULT_GENERAL_SETTINGS["auto_open_on_single_match"]


def get_default_start_screen() -> str:
    """Get default command palette start screen"""
    return DEFAULT_GENERAL_SETTINGS["start_screen"]


def get_default_always_tiles() -> bool:
    """Get default always-tiles setting"""
    return DEFAULT_GENERAL_SETTINGS["always_tiles"]


def get_supported_start_screens() -> list[str]:
    """Get list of supported start-screen values"""
    return SUPPORTED_START_SCREENS.copy()
