"""
General settings Pydantic schemas for request/response validation
"""

from pydantic import BaseModel, ConfigDict, Field
from app.core.settings.general.config.default_settings import (
    LANGUAGE_MIN_LENGTH,
    LANGUAGE_MAX_LENGTH,
    START_SCREEN_MIN_LENGTH,
    START_SCREEN_MAX_LENGTH
)


class GeneralSettingsResponse(BaseModel):
    """Response schema for general settings"""
    id: int = Field(..., description="Settings record ID")
    darkmode: bool = Field(..., description="Dark mode preference")
    language: str = Field(..., description="UI language preference")
    auto_open_on_single_match: bool = Field(
        ..., description="Auto-open the command palette's top result on a single exact match"
    )
    start_screen: str = Field(..., description="What the app index route renders: 'search' or 'newsfeed'")
    always_tiles: bool = Field(..., description="Force the command palette's touch tile grid on pointer devices")

    model_config = ConfigDict(from_attributes=True)


class GeneralSettingsUpdate(BaseModel):
    """Schema for updating general settings"""
    darkmode: bool | None = Field(None, description="Dark mode preference")
    language: str | None = Field(
        None,
        min_length=LANGUAGE_MIN_LENGTH,
        max_length=LANGUAGE_MAX_LENGTH,
        description="UI language preference"
    )


class DarkmodeUpdate(BaseModel):
    """Schema for updating only darkmode setting"""
    darkmode: bool = Field(..., description="Dark mode preference")


class LanguageUpdate(BaseModel):
    """Schema for updating only language setting"""
    language: str = Field(
        ...,
        min_length=LANGUAGE_MIN_LENGTH,
        max_length=LANGUAGE_MAX_LENGTH,
        description="UI language preference"
    )


class CommandPaletteSettingsUpdate(BaseModel):
    """Schema for updating the command palette's own settings group"""
    auto_open_on_single_match: bool | None = Field(
        None, description="Auto-open the command palette's top result on a single exact match"
    )
    start_screen: str | None = Field(
        None,
        min_length=START_SCREEN_MIN_LENGTH,
        max_length=START_SCREEN_MAX_LENGTH,
        description="What the app index route renders: 'search' or 'newsfeed'"
    )
    always_tiles: bool | None = Field(
        None, description="Force the command palette's touch tile grid on pointer devices"
    )
