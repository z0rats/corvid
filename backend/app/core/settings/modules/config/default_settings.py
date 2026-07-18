"""
Default configuration for module settings

Contains default values and configuration constants for module settings.
"""

from typing import Any


# Default values for module settings
DEFAULT_MODULE_SETTINGS: dict[str, Any] = {
    "enabled": True
}

# Available modules in the system
AVAILABLE_MODULES = [
    "cvss_calculator",
    "dork_runner",
    "domain_finder",
    "email_analyzer",
    "email_search",
    "image_tools",
    "ioc_tools",
    "llm_templates",
    "newsfeed",
    "rule_creator",
    "username_search"
]

# Module name validation constraints
MODULE_NAME_MIN_LENGTH = 1
MODULE_NAME_MAX_LENGTH = 100

# Allowed characters in module names
MODULE_NAME_ALLOWED_CHARS = set("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_-")


def get_default_enabled_status() -> bool:
    """Get default enabled status for modules"""
    return DEFAULT_MODULE_SETTINGS["enabled"]


def get_available_modules() -> list[str]:
    """Get list of available modules"""
    return AVAILABLE_MODULES.copy()


def is_valid_module_name_length(name: str) -> bool:
    """Check if module name length is valid"""
    return MODULE_NAME_MIN_LENGTH <= len(name.strip()) <= MODULE_NAME_MAX_LENGTH


def get_module_name_allowed_chars() -> set[str]:
    """Get set of allowed characters for module names"""
    return MODULE_NAME_ALLOWED_CHARS.copy()


def is_available_module(module_name: str) -> bool:
    """Check if module is in the available modules list"""
    return module_name in AVAILABLE_MODULES
