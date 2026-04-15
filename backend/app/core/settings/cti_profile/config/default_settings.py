"""
CTI Profile Default Settings Configuration

Default configuration values for CTI (Cyber Threat Intelligence) profile settings.
"""

from typing import Any


def get_default_cti_profile_settings() -> dict[str, Any]:
    """
    Generate default CTI profile settings configuration
    """
    return {
        "profile_name": "Default CTI Profile",
        "description": "Default cyber threat intelligence profile for general use",
        "threat_sources": get_default_threat_sources(),
        "indicators_of_interest": get_default_indicators(),
        "severity_threshold": "medium",
        "auto_enrichment": False,
        "notification_preferences": get_default_notification_preferences(),
        "analysis_settings": get_default_analysis_settings(),
        "retention_settings": get_default_retention_settings()
    }


def get_default_threat_sources() -> list[str]:
    """
    Get default threat intelligence sources
    """
    return [
        "mitre_attack",
        "cve_database",
        "threat_feeds",
        "osint_sources"
    ]


def get_default_indicators() -> list[str]:
    """
    Get default indicators of compromise categories
    """
    return [
        "ip_addresses",
        "domain_names",
        "file_hashes",
        "email_addresses",
        "urls",
        "registry_keys"
    ]


def get_default_notification_preferences() -> dict[str, Any]:
    """
    Get default notification preferences
    """
    return {
        "email": {
            "enabled": False,
            "recipients": [],
            "severity_filter": "high"
        },
        "webhook": {
            "enabled": False,
            "url": "",
            "headers": {},
            "severity_filter": "medium"
        },
        "dashboard": {
            "enabled": True,
            "real_time_updates": True
        }
    }


def get_default_analysis_settings() -> dict[str, Any]:
    """
    Get default analysis configuration
    """
    return {
        "correlation_enabled": True,
        "false_positive_reduction": True,
        "confidence_threshold": 0.7,
        "temporal_analysis": {
            "enabled": True,
            "time_window_hours": 24
        },
        "geolocation_analysis": {
            "enabled": True,
            "suspicious_countries": []
        }
    }


def get_default_retention_settings() -> dict[str, Any]:
    """
    Get default data retention settings
    """
    return {
        "raw_data_retention_days": 90,
        "processed_data_retention_days": 365,
        "archive_old_data": True,
        "cleanup_frequency": "weekly"
    }


def get_severity_levels() -> list[str]:
    """
    Get available severity levels
    """
    return ["low", "medium", "high", "critical"]


def get_supported_ioc_types() -> list[str]:
    """
    Get supported indicator of compromise types
    """
    return [
        "ip_addresses",
        "domain_names",
        "file_hashes",
        "email_addresses",
        "urls",
        "registry_keys",
        "file_paths",
        "mutex_names",
        "user_agents",
        "certificates"
    ]
