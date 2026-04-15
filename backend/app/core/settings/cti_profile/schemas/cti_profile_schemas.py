"""
CTI Profile Settings Schemas

Pydantic models for CTI (Cyber Threat Intelligence) profile settings validation and serialization.
"""

from pydantic import BaseModel, ConfigDict, Field, field_validator
from typing import Any


class NotificationPreferences(BaseModel):
    """Notification preferences for CTI alerts"""
    email: bool = False
    webhook: bool = False


class CTISettingsData(BaseModel):
    """CTI profile settings data structure"""
    profile_name: str = Field(..., min_length=1, max_length=100, description="Name of the CTI profile")
    threat_sources: list[str] = Field(default_factory=list, description="List of threat intelligence sources")
    indicators_of_interest: list[str] = Field(default_factory=list, description="IOCs of particular interest")
    severity_threshold: str = Field(default="medium", description="Minimum severity level for alerts")
    auto_enrichment: bool = Field(default=False, description="Enable automatic threat enrichment")
    notification_preferences: NotificationPreferences = Field(default_factory=NotificationPreferences)

    @field_validator('severity_threshold')
    @classmethod
    def validate_severity_threshold(cls, value: str) -> str:
        """Validate severity threshold value"""
        valid_severities = ["low", "medium", "high", "critical"]
        if value not in valid_severities:
            raise ValueError(f"Severity threshold must be one of: {valid_severities}")
        return value


class CTISettingsResponse(BaseModel):
    """Response model for CTI settings"""
    id: int = Field(..., description="Unique identifier for the settings")
    settings: dict[str, Any] = Field(..., description="CTI profile settings data")

    model_config = ConfigDict(from_attributes=True)


class CTISettingsUpdate(BaseModel):
    """Request model for updating CTI settings"""
    settings: dict[str, Any] = Field(..., description="Updated CTI profile settings")

    model_config = ConfigDict(from_attributes=True)


class CTISettingsCreate(BaseModel):
    """Request model for creating CTI settings"""
    settings: dict[str, Any] = Field(..., description="Initial CTI profile settings")

    model_config = ConfigDict(from_attributes=True)
