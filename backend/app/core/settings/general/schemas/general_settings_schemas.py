"""
General settings Pydantic schemas for request/response validation
"""

from pydantic import BaseModel, ConfigDict, Field
from app.core.settings.general.config.default_settings import (
    FONT_MIN_LENGTH,
    FONT_MAX_LENGTH,
    LANGUAGE_MIN_LENGTH,
    LANGUAGE_MAX_LENGTH
)


class GeneralSettingsResponse(BaseModel):
    """Response schema for general settings"""
    id: int = Field(..., description="Settings record ID")
    darkmode: bool = Field(..., description="Dark mode preference")
    font: str = Field(..., description="Font family preference")
    language: str = Field(..., description="UI language preference")

    model_config = ConfigDict(from_attributes=True)


class GeneralSettingsUpdate(BaseModel):
    """Schema for updating general settings"""
    darkmode: bool | None = Field(None, description="Dark mode preference")
    font: str | None = Field(
        None,
        min_length=FONT_MIN_LENGTH,
        max_length=FONT_MAX_LENGTH,
        description="Font family preference"
    )
    language: str | None = Field(
        None,
        min_length=LANGUAGE_MIN_LENGTH,
        max_length=LANGUAGE_MAX_LENGTH,
        description="UI language preference"
    )


class DarkmodeUpdate(BaseModel):
    """Schema for updating only darkmode setting"""
    darkmode: bool = Field(..., description="Dark mode preference")


class FontUpdate(BaseModel):
    """Schema for updating only font setting"""
    font: str = Field(
        ...,
        min_length=FONT_MIN_LENGTH,
        max_length=FONT_MAX_LENGTH,
        description="Font family preference"
    )


class LanguageUpdate(BaseModel):
    """Schema for updating only language setting"""
    language: str = Field(
        ...,
        min_length=LANGUAGE_MIN_LENGTH,
        max_length=LANGUAGE_MAX_LENGTH,
        description="UI language preference"
    )
