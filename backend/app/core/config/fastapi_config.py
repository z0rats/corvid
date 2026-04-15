from typing import Any

from .settings import settings


def get_contact_info() -> dict[str, str]:
    """Get API contact information"""
    return {
        "name": "Lars Ursprung",
        "url": "https://github.com/dev-lu",
        "email": "larsursprung@gmail.com",
    }


def get_license_info() -> dict[str, str]:
    """Get API license information"""
    return {
        "name": "MIT License",
        "url": "https://mit-license.org/",
    }


def get_tags_metadata() -> list[dict[str, str]]:
    """Get OpenAPI tags metadata for API documentation"""
    return [
        {
            "name": "System",
            "description": "Health checks and liveness/readiness probes"
        },
        {
            "name": "Alerts",
            "description": "System alert management and notifications"
        },
        {
            "name": "AI Templates", 
            "description": "LLM template management for analysis workflows"
        },
        {
            "name": "CVSS Calculator",
            "description": "CVSS vulnerability scoring calculations"
        },
        {
            "name": "Domain Lookup",
            "description": "Domain information and reputation lookup services"
        },
        {
            "name": "Email Analyzer",
            "description": "Email header analysis and security assessment"
        },
        {
            "name": "IOC Extractor",
            "description": "Extract indicators of compromise from text"
        },
        {
            "name": "IOC Lookup",
            "description": "Lookup and analyze indicators of compromise"
        },
        {
            "name": "Newsfeed",
            "description": "Security news aggregation and monitoring"
        },
        {
            "name": "Settings",
            "description": "Application configuration and preferences"
        },
    ]


def get_swagger_ui_parameters() -> dict[str, Any]:
    """Get Swagger UI configuration parameters"""
    return {
        "docExpansion": "none",
        "defaultModelsExpandDepth": -1,
        "displayRequestDuration": True,
        "filter": True,
        "showExtensions": True,
        "showCommonExtensions": True,
    }


def get_fastapi_config() -> dict[str, Any]:
    """Get complete FastAPI application configuration"""
    return {
        "title": settings.api.title,
        "version": settings.api.version,
        "description": settings.api.description,
        "contact": get_contact_info(),
        "license_info": get_license_info(),
        "openapi_tags": get_tags_metadata(),
        "swagger_ui_parameters": get_swagger_ui_parameters(),
        "debug": settings.api.debug,
        "docs_url": "/docs" if settings.environment != "production" else None,
        "redoc_url": "/redoc" if settings.environment != "production" else None,
        "openapi_url": "/openapi.json" if settings.environment != "production" else None,
    }


def get_cors_config() -> dict[str, Any]:
    """Get CORS configuration for the application"""
    if settings.environment == "production":
        return {
            "allow_origins": settings.api.cors_origins,
            "allow_credentials": False,
            "allow_methods": ["GET", "POST", "PUT", "PATCH", "DELETE"],
            "allow_headers": ["Content-Type", "Authorization"],
        }
    return {
        "allow_origins": settings.api.cors_origins,
        "allow_credentials": False,
        "allow_methods": ["*"],
        "allow_headers": ["*"],
    }
