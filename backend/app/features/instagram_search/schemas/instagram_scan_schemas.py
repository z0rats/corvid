import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.features.instagram_search.config.instagram_search_config import USERNAME_PATTERN

ScanType = Literal["followers", "followees", "posts"]


class InstagramScanRequest(BaseModel):
    """Request to scan an Instagram profile's followers, followees, or posts."""

    username: str = Field(..., min_length=1, max_length=31)
    scan_type: ScanType

    @field_validator("username")
    @classmethod
    def normalize_username(cls, v: str) -> str:
        normalized = v.strip().lstrip("@").lower()
        if not USERNAME_PATTERN.match(normalized):
            raise ValueError("Not a valid Instagram username")
        return normalized


class InstagramScanSummary(BaseModel):
    """Summary of a past scan, without its full item list."""

    id: int
    scan_type: str
    username: str
    mode: str
    status: str
    item_count: int
    total_count: int | None = None
    truncated: bool
    searched_at: datetime.datetime

    model_config = ConfigDict(from_attributes=True)


class InstagramScanDetail(InstagramScanSummary):
    """Full detail of a past scan, including its persisted items.

    `items` shape depends on `scan_type`: `followers`/`followees` items carry
    `username`/`full_name`; `posts` items carry `shortcode`/`permalink`/
    `date_utc`/`is_video`/`likes`/`comments`/`caption`. Left as a loose
    `dict` list rather than a typed union - the frontend already branches on
    `scan_type` to render either shape, so a second, harder-to-evolve type
    boundary here wouldn't buy anything beyond what the DB's JSON blob already
    is (see GitReconResult for the case where structure *does* pay for itself).
    """

    error: str | None = None
    items: list[dict[str, Any]] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)
