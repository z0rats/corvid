from pathlib import Path
from typing import Any
import logging

from .settings import settings


def validate_directory_exists(path: str, create_if_missing: bool = True) -> bool:
    """Validate that a directory exists, optionally create it"""
    directory = Path(path)
    
    if directory.exists() and directory.is_dir():
        return True
    
    if create_if_missing:
        try:
            directory.mkdir(parents=True, exist_ok=True)
            return True
        except Exception as e:
            logging.error("Failed to create directory %s: %s", path, e)
            return False
    
    return False



def validate_database_settings() -> list[str]:
    """Validate database configuration settings"""
    errors = []
    
    if not settings.database.url:
        errors.append("Database URL is not configured")
    
    if settings.database.pool_size <= 0:
        errors.append("Database pool size must be greater than 0")
    
    if settings.database.max_overflow < 0:
        errors.append("Database max overflow cannot be negative")
    
    # Validate SQLite database directory exists
    if settings.database.url.startswith("sqlite"):
        db_path = settings.database.url.replace("sqlite:///", "")
        db_dir = Path(db_path).parent
        if not validate_directory_exists(str(db_dir)):
            errors.append(f"Database directory does not exist: {db_dir}")
    
    return errors


def validate_logging_settings() -> list[str]:
    """Validate logging configuration settings"""
    errors = []
    
    valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
    if settings.logging.level.upper() not in valid_levels:
        errors.append(f"Invalid logging level: {settings.logging.level}")
    
    if not validate_directory_exists(settings.logging.dir):
        errors.append(f"Logging directory cannot be created: {settings.logging.dir}")
    
    if settings.logging.max_file_size <= 0:
        errors.append("Log file max size must be greater than 0")
    
    if settings.logging.backup_count < 0:
        errors.append("Log backup count cannot be negative")
    
    return errors


def validate_api_settings() -> list[str]:
    """Validate API configuration settings"""
    errors = []
    
    if not settings.api.title:
        errors.append("API title is not configured")
    
    if not settings.api.version:
        errors.append("API version is not configured")
    
    if not isinstance(settings.api.cors_origins, list):
        errors.append("CORS origins must be a list")
    
    return errors


def validate_environment_variables() -> list[str]:
    """Validate required environment variables"""
    errors = []

    if settings.environment == "production":
        if settings.api.debug:
            errors.append("Debug mode should be disabled in production")

        if "*" in settings.api.cors_origins:
            errors.append("CORS origins should be restricted in production")

        default_cors_origins = ["http://localhost:3000"]
        if settings.api.cors_origins == default_cors_origins:
            errors.append(
                "CORS origins are still at the localhost development default "
                f"({default_cors_origins}) while ENVIRONMENT=production — set "
                "API_CORS_ORIGINS to the actual origin(s) this is served from"
            )

        default_trusted_hosts = ["localhost", "127.0.0.1"]
        if settings.api.trusted_hosts == default_trusted_hosts:
            errors.append(
                "Trusted hosts are still at the localhost development default "
                f"({default_trusted_hosts}) while ENVIRONMENT=production — set "
                "API_TRUSTED_HOSTS to the actual host(s) this is served from, or "
                "requests may be rejected by TrustedHostMiddleware"
            )

    return errors


def validate_security_settings() -> list[str]:
    """Validate security-related configuration settings"""
    errors = []

    if settings.security.allow_private_network_targets:
        errors.append(
            "SECURITY_ALLOW_PRIVATE_NETWORK_TARGETS is enabled — the SSRF guard will "
            "allow outbound requests to private/loopback/link-local/reserved targets. "
            "Dev/testing only; disable this in any deployment reachable from a "
            "sensitive network"
        )

    return errors


def validate_all_settings() -> dict[str, list[str]]:
    """Validate all configuration settings"""
    validation_results = {
        "database": validate_database_settings(),
        "logging": validate_logging_settings(),
        "api": validate_api_settings(),
        "environment": validate_environment_variables(),
        "security": validate_security_settings(),
    }
    
    return validation_results


def get_validation_summary() -> dict[str, Any]:
    """Get a summary of configuration validation"""
    results = validate_all_settings()
    
    total_errors = sum(len(errors) for errors in results.values())
    has_errors = total_errors > 0
    
    return {
        "valid": not has_errors,
        "total_errors": total_errors,
        "results": results,
        "summary": f"Configuration validation {'failed' if has_errors else 'passed'} with {total_errors} error(s)"
    }


def log_validation_results() -> None:
    """Log configuration validation results"""
    logger = logging.getLogger(__name__)
    summary = get_validation_summary()
    
    if summary["valid"]:
        logger.info("Configuration validation passed successfully")
    else:
        logger.error("Configuration validation failed with %s error(s)", summary['total_errors'])
        
        for category, errors in summary["results"].items():
            if errors:
                logger.error("%s configuration errors:", category.title())
                for error in errors:
                    logger.error("  - %s", error)


def ensure_required_directories() -> None:
    """Ensure all required directories exist"""
    directories = [
        settings.data_dir,
        settings.logging.dir,
        settings.static_dir,
    ]
    
    for directory in directories:
        validate_directory_exists(directory, create_if_missing=True)
