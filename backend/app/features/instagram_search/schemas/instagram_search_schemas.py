from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field, field_validator

from app.features.instagram_search.config.instagram_search_config import USERNAME_PATTERN

InstagramLookupMode = Literal["anonymous", "session"]


class InstagramProfileRequest(BaseModel):
    """Request to look up a public Instagram profile's metadata by username."""

    username: str = Field(
        ...,
        min_length=1,
        max_length=31,
        description="Instagram username, with or without a leading @",
    )

    @field_validator("username")
    @classmethod
    def normalize_username(cls, v: str) -> str:
        normalized = v.strip().lstrip("@").lower()
        if not USERNAME_PATTERN.match(normalized):
            raise ValueError("Not a valid Instagram username")
        return normalized


class InstagramProfileResponse(BaseModel):
    """Public Instagram profile metadata, as returned by Instaloader's `Profile`."""

    username: str
    userid: int | None = None
    full_name: str | None = None
    biography: str | None = None
    biography_hashtags: list[str] = Field(default_factory=list)
    biography_mentions: list[str] = Field(default_factory=list)
    external_url: str | None = None
    followers: int | None = None
    followees: int | None = None
    mediacount: int | None = None
    igtvcount: int | None = None
    is_private: bool = False
    is_verified: bool = False
    is_business_account: bool = False
    business_category_name: str | None = None
    has_public_story: bool = False
    has_highlight_reels: bool = False
    profile_pic_url: str | None = None
    mode: InstagramLookupMode = "anonymous"
    timestamp: datetime


class InstagramHealthResponse(BaseModel):
    """Instaloader installation status, surfaced under Settings/module health."""

    installed_version: str
    latest_pypi_version: str | None = None
    update_available: bool | None = Field(
        default=None, description="None if the PyPI check hasn't run or failed"
    )
    session_configured: bool = Field(
        default=False, description="Whether an active, well-formed Instagram session is set"
    )
