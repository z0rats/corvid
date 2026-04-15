"""
CTI Profile Utilities

Utility functions for CTI (Cyber Threat Intelligence) profile operations.
"""

from typing import Any
from datetime import datetime, timedelta
import re
import logging

logger = logging.getLogger(__name__)


def sanitize_profile_name(profile_name: str) -> str:
    """
    Sanitize and validate CTI profile name
    """
    if not profile_name or not isinstance(profile_name, str):
        raise ValueError("Profile name must be a non-empty string")
    
    # Remove leading/trailing whitespace
    sanitized = profile_name.strip()
    
    # Check minimum length
    if len(sanitized) < 1:
        raise ValueError("Profile name cannot be empty")
    
    # Check maximum length
    if len(sanitized) > 100:
        raise ValueError("Profile name cannot exceed 100 characters")
    
    # Remove potentially harmful characters
    sanitized = re.sub(r'[<>"\']', '', sanitized)
    
    return sanitized


def validate_ioc_format(ioc_value: str, ioc_type: str) -> bool:
    """
    Validate indicator of compromise format based on type
    """
    if not ioc_value or not isinstance(ioc_value, str):
        return False
    
    validation_patterns = {
        "ip_addresses": r'^(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$',
        "domain_names": r'^[a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?(\.[a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?)*$',
        "email_addresses": r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$',
        "file_hashes": r'^[a-fA-F0-9]{32}$|^[a-fA-F0-9]{40}$|^[a-fA-F0-9]{64}$',
        "urls": r'^https?://[^\s/$.?#].[^\s]*$'
    }
    
    pattern = validation_patterns.get(ioc_type)
    if not pattern:
        logger.warning("No validation pattern for IOC type: %s", ioc_type)
        return True  # Allow unknown types for flexibility
    
    return bool(re.match(pattern, ioc_value))


def merge_settings_with_defaults(
    user_settings: dict[str, Any], 
    default_settings: dict[str, Any]
) -> dict[str, Any]:
    """
    Merge user settings with default settings, preserving user preferences
    """
    merged = default_settings.copy()
    
    for key, value in user_settings.items():
        if isinstance(value, dict) and key in merged and isinstance(merged[key], dict):
            # Recursively merge nested dictionaries
            merged[key] = merge_settings_with_defaults(value, merged[key])
        else:
            # Override with user value
            merged[key] = value
    
    return merged


def calculate_threat_score(
    indicators: list[str],
    severity_weights: dict[str, float] | None = None
) -> float:
    """
    Calculate a threat score based on indicators and severity weights
    """
    if not indicators:
        return 0.0
    
    if severity_weights is None:
        severity_weights = {
            "critical": 1.0,
            "high": 0.8,
            "medium": 0.6,
            "low": 0.4
        }
    
    # Simple scoring algorithm
    base_score = len(indicators) * 0.1
    max_score = min(base_score, 1.0)
    
    return round(max_score, 2)


def format_settings_for_display(settings: dict[str, Any]) -> dict[str, Any]:
    """
    Format settings for frontend display with human-readable values
    """
    formatted = settings.copy()
    
    # Format timestamps if present
    for key in ["created_at", "updated_at"]:
        if key in formatted and formatted[key]:
            try:
                if isinstance(formatted[key], str):
                    dt = datetime.fromisoformat(formatted[key].replace('Z', '+00:00'))
                    formatted[key] = dt.strftime("%Y-%m-%d %H:%M:%S UTC")
            except (ValueError, AttributeError):
                logger.warning("Failed to format timestamp for key: %s", key)
    
    # Format severity threshold
    if "severity_threshold" in formatted:
        severity_map = {
            "low": "Low Priority",
            "medium": "Medium Priority", 
            "high": "High Priority",
            "critical": "Critical Priority"
        }
        threshold = formatted["severity_threshold"]
        formatted["severity_threshold_display"] = severity_map.get(threshold, threshold.title())
    
    # Format boolean values
    if "auto_enrichment" in formatted:
        formatted["auto_enrichment_display"] = "Enabled" if formatted["auto_enrichment"] else "Disabled"
    
    return formatted


def validate_retention_settings(retention_settings: dict[str, Any]) -> bool:
    """
    Validate data retention settings
    """
    required_fields = ["raw_data_retention_days", "processed_data_retention_days"]
    
    for field in required_fields:
        if field not in retention_settings:
            logger.error("Missing required retention field: %s", field)
            return False
        
        value = retention_settings[field]
        if not isinstance(value, int) or value < 1:
            logger.error("Invalid retention value for %s: %s", field, value)
            return False
    
    # Ensure processed data retention is not less than raw data retention
    raw_retention = retention_settings["raw_data_retention_days"]
    processed_retention = retention_settings["processed_data_retention_days"]
    
    if processed_retention < raw_retention:
        logger.error("Processed data retention cannot be less than raw data retention")
        return False
    
    return True


def generate_settings_summary(settings: dict[str, Any]) -> str:
    """
    Generate a human-readable summary of CTI profile settings
    """
    profile_name = settings.get("profile_name", "Unknown Profile")
    severity = settings.get("severity_threshold", "medium").title()
    
    threat_sources_count = len(settings.get("threat_sources", []))
    indicators_count = len(settings.get("indicators_of_interest", []))
    
    auto_enrichment = "enabled" if settings.get("auto_enrichment", False) else "disabled"
    
    summary = (
        f"CTI Profile: {profile_name}\n"
        f"Severity Threshold: {severity}\n"
        f"Threat Sources: {threat_sources_count} configured\n"
        f"Indicators of Interest: {indicators_count} types\n"
        f"Auto-enrichment: {auto_enrichment}"
    )
    
    return summary
