"""
CTI Profile Settings Module

This module provides CTI (Cyber Threat Intelligence) profile settings management
functionality including database models, API routes, business logic, and utilities.

Module Structure:
- config/: Default configuration values and constants
- crud/: Repository pattern implementation for data access
- models/: SQLAlchemy database models
- routers/: FastAPI route definitions
- schemas/: Pydantic models for validation and serialization
- service/: Business logic layer
- utils/: Utility functions for CTI operations
"""

from .routers.cti_profile_routes import router as cti_profile_router
from .schemas.cti_profile_schemas import (
    CTISettingsResponse,
    CTISettingsUpdate,
    CTISettingsCreate,
    CTISettingsData,
    NotificationPreferences
)
from .service.cti_profile_service import (
    get_cti_profile_settings,
    update_cti_profile_settings
)
from .config.default_settings import (
    get_default_cti_profile_settings,
    get_severity_levels,
    get_supported_ioc_types
)

__all__ = [
    # Router
    "cti_profile_router",
    
    # Schemas
    "CTISettingsResponse",
    "CTISettingsUpdate", 
    "CTISettingsCreate",
    "CTISettingsData",
    "NotificationPreferences",
    
    # Services
    "get_cti_profile_settings",
    "update_cti_profile_settings",
    
    # Configuration
    "get_default_cti_profile_settings",
    "get_severity_levels",
    "get_supported_ioc_types"
]
