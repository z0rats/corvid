"""
Domain validation utility functions
"""
import re
from urllib.parse import urlparse
import logging

logger = logging.getLogger(__name__)


def sanitize_domain_input(domain: str) -> str:
    """
    Sanitize and normalize domain input by removing protocols, paths, and ports
    
    Args:
        domain: Raw domain input string
        
    Returns:
        Cleaned domain string
    """
    if not domain:
        return ""
    
    original_domain = domain
    domain = domain.strip().lower()
    
    # Remove protocol if present
    if domain.startswith(('http://', 'https://')):
        parsed = urlparse(domain)
        domain = parsed.netloc or parsed.path
        logger.debug("Removed protocol: '%s' -> '%s'", original_domain, domain)
    
    # Remove path, query, and fragment components
    domain = domain.split('/')[0].split('?')[0].split('#')[0]
    
    # Remove port if present (but not for IPv6)
    if ':' in domain and not domain.count(':') > 1:
        domain = domain.split(':')[0]
        logger.debug("Removed port: '%s'", domain)
    
    logger.debug("Domain sanitization completed: '%s' -> '%s'", original_domain, domain)
    return domain


def validate_domain_format(domain: str) -> bool:
    """
    Validate domain format using regex patterns, supporting search patterns
    
    Args:
        domain: Domain string to validate
        
    Returns:
        True if domain format is valid or is a valid search pattern
    """
    if not domain or len(domain) > 255:
        return False
    
    # Check if this is a search pattern (contains wildcards)
    is_search_pattern = '*' in domain or '?' in domain
    
    if is_search_pattern:
        # Allow alphanumeric, dots, hyphens, underscores, and wildcards
        search_pattern = re.compile(r'^[a-zA-Z0-9.\-_*?]+$')
        return bool(search_pattern.match(domain))
    else:
        # Standard domain regex pattern
        domain_pattern = re.compile(
            r'^(?:[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?\.)*[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?$'
        )
        return bool(domain_pattern.match(domain))


def validate_ip_address_format(value: str) -> bool:
    """
    Check if the value is a valid IP address format
    
    Args:
        value: String to validate as IP address
        
    Returns:
        True if value is a valid IP address
    """
    # IPv4 pattern
    ipv4_pattern = re.compile(
        r'^(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$'
    )
    
    # IPv6 pattern (simplified)
    ipv6_pattern = re.compile(
        r'^(?:[0-9a-fA-F]{1,4}:){7}[0-9a-fA-F]{1,4}$|^::1$|^::$'
    )
    
    return bool(ipv4_pattern.match(value) or ipv6_pattern.match(value))


def extract_root_domain_from_subdomain(domain: str) -> str:
    """
    Extract root domain from a full domain including subdomains
    
    Args:
        domain: Full domain including potential subdomains
        
    Returns:
        Root domain (e.g., 'example.com' from 'www.sub.example.com')
    """
    if not domain:
        return ""
    
    parts = domain.split('.')
    
    # Handle cases with at least 2 parts
    if len(parts) >= 2:
        return '.'.join(parts[-2:])
    
    return domain


def validate_and_format_domain_for_api(domain: str) -> str:
    """
    Validate and format domain for API requests, supporting search patterns
    
    Args:
        domain: Domain to validate and format
        
    Returns:
        Formatted domain suitable for API requests
        
    Raises:
        ValueError: If domain format is invalid
    """
    logger.debug("Validating and formatting domain: '%s'", domain)
    original_domain = domain
    
    # Check if this is a search pattern before sanitization
    is_search_pattern = '*' in domain or '?' in domain
    
    if is_search_pattern:
        # For search patterns, do minimal sanitization to preserve wildcards
        domain = domain.strip().lower()
    else:
        # For regular domains, do full sanitization
        domain = sanitize_domain_input(domain)
    
    is_valid_domain = validate_domain_format(domain)
    is_valid_ip = validate_ip_address_format(domain) if not is_search_pattern else False
    
    if not is_valid_domain and not is_valid_ip:
        error_msg = f"Invalid search pattern format: {domain}" if is_search_pattern else f"Invalid domain or IP address format: {domain}"
        logger.error("%s (original: '%s')", error_msg, original_domain)
        raise ValueError(error_msg)
    
    logger.debug("Domain validation successful: '%s' -> '%s'", original_domain, domain)
    return domain
