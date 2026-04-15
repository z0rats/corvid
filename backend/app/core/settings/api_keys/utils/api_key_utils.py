from typing import Any
import re
import logging
from datetime import datetime, timezone

from app.core.settings.api_keys.models.api_keys_settings_models import Apikey


def validate_api_key_name(name: str) -> bool:
    """
    Validate API key name format.
    
    Args:
        name: The API key name to validate
        
    Returns:
        True if valid, False otherwise
    """
    if not name or not isinstance(name, str):
        return False
    
    # Check length
    if len(name.strip()) == 0 or len(name.strip()) > 100:
        return False
    
    # Check for valid characters (alphanumeric, underscore, hyphen)
    pattern = r'^[a-zA-Z0-9_-]+$'
    return bool(re.match(pattern, name.strip()))


def validate_api_key_value(key: str) -> bool:
    """
    Validate API key value format.
    
    Args:
        key: The API key value to validate
        
    Returns:
        True if valid, False otherwise
    """
    if not isinstance(key, str):
        return False
    
    # Allow empty keys (for placeholder entries)
    if len(key.strip()) == 0:
        return True
    
    # Check length
    if len(key.strip()) > 500:
        return False
    
    # Basic format validation (no whitespace, printable characters)
    return key.strip() == key and key.isprintable()


def sanitize_api_key_name(name: str) -> str:
    """
    Sanitize and normalize API key name.
    
    Args:
        name: The API key name to sanitize
        
    Returns:
        Sanitized name
    """
    if not name or not isinstance(name, str):
        return ""
    
    # Strip whitespace and convert to lowercase
    sanitized = name.strip().lower()
    
    # Replace invalid characters with underscores
    sanitized = re.sub(r'[^a-zA-Z0-9_-]', '_', sanitized)
    
    # Remove multiple consecutive underscores
    sanitized = re.sub(r'_+', '_', sanitized)
    
    # Remove leading/trailing underscores
    sanitized = sanitized.strip('_')
    
    return sanitized[:100]  # Truncate to max length


def mask_api_key(key: str, visible_chars: int = 4) -> str:
    """
    Mask an API key for display purposes.
    
    Args:
        key: The API key to mask
        visible_chars: Number of characters to show at the end
        
    Returns:
        Masked API key string
    """
    if not key or not isinstance(key, str):
        return ""
    
    key = key.strip()
    if len(key) <= visible_chars:
        return "*" * len(key)
    
    return "*" * (len(key) - visible_chars) + key[-visible_chars:]


def categorize_api_keys(api_keys: list[Apikey]) -> dict[str, list[Apikey]]:
    """
    Categorize API keys by their status.
    
    Args:
        api_keys: List of API key models
        
    Returns:
        Dictionary with categorized API keys
    """
    categories = {
        'configured': [],
        'unconfigured': [],
        'active': [],
        'inactive': [],
        'bulk_enabled': [],
        'bulk_disabled': []
    }
    
    for key in api_keys:
        # Configuration status
        if key.is_configured():
            categories['configured'].append(key)
        else:
            categories['unconfigured'].append(key)
        
        # Active status
        if key.is_active:
            categories['active'].append(key)
        else:
            categories['inactive'].append(key)
        
        # Bulk lookup status
        if key.bulk_ioc_lookup:
            categories['bulk_enabled'].append(key)
        else:
            categories['bulk_disabled'].append(key)
    
    return categories


def generate_api_key_report(api_keys: list[Apikey]) -> dict[str, Any]:
    """
    Generate a comprehensive report about API key status.
    
    Args:
        api_keys: List of API key models
        
    Returns:
        Dictionary containing the report
    """
    categories = categorize_api_keys(api_keys)
    
    report = {
        'timestamp': datetime.now(timezone.utc).isoformat(),
        'total_keys': len(api_keys),
        'summary': {
            'configured': len(categories['configured']),
            'unconfigured': len(categories['unconfigured']),
            'active': len(categories['active']),
            'inactive': len(categories['inactive']),
            'bulk_enabled': len(categories['bulk_enabled']),
            'usable': len([key for key in api_keys if key.is_usable()])
        },
        'percentages': {},
        'details': {}
    }
    
    # Calculate percentages
    total = report['total_keys']
    if total > 0:
        report['percentages'] = {
            'configured': round((report['summary']['configured'] / total) * 100, 1),
            'active': round((report['summary']['active'] / total) * 100, 1),
            'usable': round((report['summary']['usable'] / total) * 100, 1)
        }
    
    # Add detailed information
    report['details'] = {
        'configured_keys': [key.name for key in categories['configured']],
        'unconfigured_keys': [key.name for key in categories['unconfigured']],
        'active_keys': [key.name for key in categories['active']],
        'usable_keys': [key.name for key in api_keys if key.is_usable()]
    }
    
    return report


def find_duplicate_keys(api_keys: list[Apikey]) -> dict[str, list[str]]:
    """
    Find API keys that have duplicate values.
    
    Args:
        api_keys: List of API key models
        
    Returns:
        Dictionary mapping key values to lists of key names that use them
    """
    key_map = {}
    duplicates = {}
    
    for api_key in api_keys:
        if api_key.key and api_key.key.strip():
            key_value = api_key.key.strip()
            if key_value not in key_map:
                key_map[key_value] = []
            key_map[key_value].append(api_key.name)
    
    # Find duplicates
    for key_value, names in key_map.items():
        if len(names) > 1:
            duplicates[key_value] = names
    
    return duplicates


def get_api_key_health_score(api_keys: list[Apikey]) -> float:
    """
    Calculate a health score for the API key configuration.
    
    Args:
        api_keys: List of API key models
        
    Returns:
        Health score between 0.0 and 1.0
    """
    if not api_keys:
        return 0.0
    
    total_keys = len(api_keys)
    configured_keys = len([key for key in api_keys if key.is_configured()])
    active_keys = len([key for key in api_keys if key.is_active])
    usable_keys = len([key for key in api_keys if key.is_usable()])
    
    # Weight different factors
    configuration_score = configured_keys / total_keys * 0.4
    active_score = active_keys / total_keys * 0.3
    usability_score = usable_keys / total_keys * 0.3
    
    return configuration_score + active_score + usability_score


def log_api_key_operation(operation: str, key_name: str, success: bool, details: str | None = None) -> None:
    """
    Log API key operations for audit purposes.
    
    Args:
        operation: The operation performed (create, update, delete, etc.)
        key_name: Name of the API key
        success: Whether the operation was successful
        details: Additional details about the operation
    """
    level = logging.INFO if success else logging.ERROR
    status = "SUCCESS" if success else "FAILED"
    
    message = f"API Key {operation.upper()}: {key_name} - {status}"
    if details:
        message += f" - {details}"
    
    logging.log(level, message)


def format_api_key_for_display(api_key: Apikey, include_key: bool = False) -> dict[str, Any]:
    """
    Format an API key for safe display in UI or logs.
    
    Args:
        api_key: The API key model
        include_key: Whether to include the (masked) key value
        
    Returns:
        Dictionary with formatted API key information
    """
    formatted = {
        'name': api_key.name,
        'is_active': api_key.is_active,
        'bulk_ioc_lookup': api_key.bulk_ioc_lookup,
        'is_configured': api_key.is_configured(),
        'is_usable': api_key.is_usable(),
        'created_at': api_key.created_at.isoformat() if api_key.created_at else None,
        'updated_at': api_key.updated_at.isoformat() if api_key.updated_at else None
    }
    
    if include_key:
        formatted['key'] = mask_api_key(api_key.key) if api_key.key else ""
    
    return formatted
