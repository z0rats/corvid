from typing import Any
import logging

logger = logging.getLogger(__name__)

# Default rate limiting configuration
DEFAULT_RATE_LIMITS = {
    # Default rate limit for services not explicitly configured
    'default': 2.0,
    
    # Service-specific rate limits (requests per second)
    'virustotal': 4.0,      # VirusTotal Public API: 4 req/sec
    'abuseipdb': 1.0,       # AbuseIPDB: 1 req/sec for free tier
    'shodan': 1.0,          # Shodan: 1 req/sec for free tier
    'urlvoid': 1.0,         # URLVoid: 1 req/sec
    'hybrid_analysis': 2.0, # Hybrid Analysis: 2 req/sec
    'otx': 3.0,            # AlienVault OTX: 3 req/sec
    'threatminer': 2.0,     # ThreatMiner: 2 req/sec
    'censys': 1.0,         # Censys: 1 req/sec for free tier
    'greynoise': 2.0,      # GreyNoise: 2 req/sec
    'ipqualityscore': 1.5, # IPQualityScore: 1.5 req/sec
}

# Concurrency limits
CONCURRENCY_LIMITS = {
    'max_concurrent_requests': 10,  # Maximum concurrent requests across all services
    'max_concurrent_per_service': 3,  # Maximum concurrent requests per service
}

# Retry configuration for rate-limited requests
RETRY_CONFIG = {
    'max_retries': 3,
    'base_delay': 1.0,      # Base delay in seconds
    'max_delay': 30.0,      # Maximum delay in seconds
    'backoff_factor': 2.0,  # Exponential backoff factor
}

# Timeout configuration
TIMEOUT_CONFIG = {
    'request_timeout': 30.0,    # Individual request timeout in seconds
    'total_timeout': 300.0,     # Total bulk operation timeout in seconds
}


def get_service_rate_limit(service_name: str) -> float:
    """
    Get the rate limit for a specific service
    
    Args:
        service_name: Name of the service
        
    Returns:
        Rate limit in requests per second
    """
    rate_limit = DEFAULT_RATE_LIMITS.get(service_name, DEFAULT_RATE_LIMITS['default'])
    logger.debug("Rate limit for %s: %s req/sec", service_name, rate_limit)
    return rate_limit


def get_concurrency_limit(limit_type: str = 'max_concurrent_requests') -> int:
    """
    Get concurrency limits
    
    Args:
        limit_type: Type of limit to retrieve
        
    Returns:
        Concurrency limit value
    """
    return CONCURRENCY_LIMITS.get(limit_type, CONCURRENCY_LIMITS['max_concurrent_requests'])


def get_retry_config() -> dict[str, Any]:
    """
    Get retry configuration
    
    Returns:
        Dictionary containing retry configuration
    """
    return RETRY_CONFIG.copy()


def get_timeout_config() -> dict[str, float]:
    """
    Get timeout configuration
    
    Returns:
        Dictionary containing timeout configuration
    """
    return TIMEOUT_CONFIG.copy()


def update_service_rate_limit(service_name: str, rate_limit: float) -> None:
    """
    Update rate limit for a specific service (runtime configuration)
    
    Args:
        service_name: Name of the service
        rate_limit: New rate limit in requests per second
    """
    if rate_limit <= 0:
        raise ValueError("Rate limit must be positive")
    
    DEFAULT_RATE_LIMITS[service_name] = rate_limit
    logger.info("Updated rate limit for %s: %s req/sec", service_name, rate_limit)


def get_all_rate_limits() -> dict[str, float]:
    """
    Get all configured rate limits
    
    Returns:
        Dictionary of all service rate limits
    """
    return DEFAULT_RATE_LIMITS.copy()


def validate_rate_limit_config() -> bool:
    """
    Validate the rate limiting configuration
    
    Returns:
        True if configuration is valid, False otherwise
    """
    try:
        # Check that all rate limits are positive numbers
        for service, rate_limit in DEFAULT_RATE_LIMITS.items():
            if not isinstance(rate_limit, (int, float)) or rate_limit <= 0:
                logger.error("Invalid rate limit for %s: %s", service, rate_limit)
                return False
        
        # Check concurrency limits
        for limit_type, limit_value in CONCURRENCY_LIMITS.items():
            if not isinstance(limit_value, int) or limit_value <= 0:
                logger.error("Invalid concurrency limit for %s: %s", limit_type, limit_value)
                return False
        
        # Check retry configuration
        if RETRY_CONFIG['max_retries'] < 0:
            logger.error("Invalid max_retries: %s", RETRY_CONFIG['max_retries'])
            return False
        
        if RETRY_CONFIG['base_delay'] <= 0:
            logger.error("Invalid base_delay: %s", RETRY_CONFIG['base_delay'])
            return False
        
        if RETRY_CONFIG['backoff_factor'] <= 1.0:
            logger.error("Invalid backoff_factor: %s", RETRY_CONFIG['backoff_factor'])
            return False
        
        # Check timeout configuration
        for timeout_type, timeout_value in TIMEOUT_CONFIG.items():
            if not isinstance(timeout_value, (int, float)) or timeout_value <= 0:
                logger.error("Invalid timeout for %s: %s", timeout_type, timeout_value)
                return False
        
        logger.info("Rate limiting configuration validation passed")
        return True
        
    except Exception as e:
        logger.error("Error validating rate limiting configuration: %s", str(e))
        return False


# Validate configuration on import
if not validate_rate_limit_config():
    logger.warning("Rate limiting configuration validation failed, using defaults")
