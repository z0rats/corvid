"""
Default configuration for keywords settings

Contains default values and configuration constants for keyword management.
"""

from typing import Any


# Default keywords for initial setup
DEFAULT_KEYWORDS: list[str] = [
    "malware",
    "phishing",
    "ransomware",
    "vulnerability",
    "exploit",
    "breach",
    "attack",
    "threat",
    "security",
    "cybersecurity"
]

KEYWORD_CONFIG: dict[str, Any] = {
    "max_keywords": 1000,
    "default_pagination_limit": 100,
    "max_pagination_limit": 500,
    "enable_auto_normalization": True,
    "case_sensitive": False
}

KEYWORD_CATEGORIES: dict[str, list[str]] = {
    "threats": ["malware", "phishing", "ransomware", "trojan", "virus"],
    "vulnerabilities": ["cve", "exploit", "vulnerability", "zero-day", "patch"],
    "incidents": ["breach", "attack", "compromise", "incident", "leak"],
    "general": ["security", "cybersecurity", "infosec", "threat", "risk"]
}

KEYWORD_PRIORITIES: dict[str, int] = {
    "critical": 1,
    "high": 2,
    "medium": 3,
    "low": 4,
    "info": 5
}


def get_default_keywords() -> list[str]:
    """
    Get list of default keywords for initial setup
    
    Returns:
        List[str]: List of default keywords
    """
    return DEFAULT_KEYWORDS.copy()


def get_max_keywords() -> int:
    """
    Get maximum number of keywords allowed
    
    Returns:
        int: Maximum keyword count
    """
    return KEYWORD_CONFIG["max_keywords"]


def get_default_pagination_limit() -> int:
    """
    Get default pagination limit for keyword lists
    
    Returns:
        int: Default pagination limit
    """
    return KEYWORD_CONFIG["default_pagination_limit"]


def get_max_pagination_limit() -> int:
    """
    Get maximum pagination limit for keyword lists
    
    Returns:
        int: Maximum pagination limit
    """
    return KEYWORD_CONFIG["max_pagination_limit"]


def is_auto_normalization_enabled() -> bool:
    """
    Check if automatic keyword normalization is enabled
    
    Returns:
        bool: True if auto-normalization is enabled
    """
    return KEYWORD_CONFIG["enable_auto_normalization"]


def is_case_sensitive() -> bool:
    """
    Check if keyword matching is case sensitive
    
    Returns:
        bool: True if case sensitive matching is enabled
    """
    return KEYWORD_CONFIG["case_sensitive"]


def get_keyword_categories() -> dict[str, list[str]]:
    """
    Get keyword categories mapping
    
    Returns:
        Dict[str, List[str]]: Dictionary of categories and their keywords
    """
    return {category: keywords.copy() for category, keywords in KEYWORD_CATEGORIES.items()}


def get_keyword_priorities() -> dict[str, int]:
    """
    Get keyword priority levels
    
    Returns:
        Dict[str, int]: Dictionary of priority names and levels
    """
    return KEYWORD_PRIORITIES.copy()


def get_keyword_config() -> dict[str, Any]:
    """
    Get complete keyword configuration
    
    Returns:
        Dict[str, Any]: Complete configuration dictionary
    """
    return KEYWORD_CONFIG.copy()


def validate_pagination_limit(limit: int) -> int:
    """
    Validate and adjust pagination limit within allowed bounds
    
    Args:
        limit: Requested pagination limit
        
    Returns:
        int: Validated pagination limit
    """
    max_limit = get_max_pagination_limit()
    default_limit = get_default_pagination_limit()
    
    if limit <= 0:
        return default_limit
    
    return min(limit, max_limit)
