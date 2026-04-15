"""Pydantic schemas for keywords settings"""

import re
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator


class KeywordBase(BaseModel):
    """Base keyword schema with common fields"""
    keyword: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="The keyword string",
        json_schema_extra={"examples": ["malware"]}
    )

    @field_validator('keyword')
    @classmethod
    def validate_keyword_format(cls, v: str) -> str:
        """Validate keyword format and normalize"""
        if not v or not v.strip():
            raise ValueError('Keyword cannot be empty')

        if not re.match(r'^[a-zA-Z0-9\s\-_]+$', v.strip()):
            raise ValueError('Keyword contains invalid characters. Only letters, numbers, spaces, hyphens, and underscores are allowed')

        return re.sub(r'\s+', ' ', v.strip().lower())


class KeywordCreate(KeywordBase):
    """
    Schema for creating a new keyword
    """
    pass


class KeywordUpdate(KeywordBase):
    """
    Schema for updating an existing keyword
    """
    pass


class KeywordResponse(KeywordBase):
    """
    Schema for keyword responses
    """
    id: int = Field(..., description="Unique identifier for the keyword")
    created_at: datetime | None = Field(None, description="Timestamp when keyword was created")
    updated_at: datetime | None = Field(None, description="Timestamp when keyword was last updated")

    model_config = ConfigDict(from_attributes=True)


class KeywordListResponse(BaseModel):
    """
    Schema for paginated keyword list responses
    """
    keywords: list[KeywordResponse] = Field(..., description="List of keywords")
    total: int = Field(..., description="Total number of keywords")
    skip: int = Field(..., description="Number of keywords skipped")
    limit: int = Field(..., description="Maximum number of keywords returned")

    model_config = ConfigDict(from_attributes=True)


class KeywordDeleteResponse(BaseModel):
    """
    Schema for keyword deletion responses
    """
    detail: str = Field(..., description="Success message", json_schema_extra={"examples": ["Keyword deleted successfully"]})


class KeywordValidationError(BaseModel):
    """
    Schema for keyword validation error responses
    """
    detail: str = Field(..., description="Error message")
    field: str | None = Field(None, description="Field that caused the error")
    invalid_value: str | None = Field(None, description="The invalid value that was provided")
