import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator


class ScanRequest(BaseModel):
    """Request to start a new username search"""

    username: str = Field(..., description="Username to search for", min_length=1, max_length=100)
    source: Literal["maigret", "social_analyzer"] = Field(default="maigret", description="Which search tool to use")
    tags: list[str] | None = Field(default=None, description="Only scan sites with at least one of these tags (maigret only)")
    excluded_tags: list[str] | None = Field(default=None, description="Skip sites with any of these tags (maigret only)")

    @field_validator("username")
    @classmethod
    def validate_username(cls, v: str) -> str:
        username = v.strip()
        if not username:
            raise ValueError("Username cannot be empty")
        return username


class SiteResultSchema(BaseModel):
    """A single claimed/found site result"""

    site_name: str = Field(..., description="Name of the site where the username was found")
    url_user: str = Field(..., description="URL of the found profile")
    http_status: int | None = Field(default=None, description="HTTP status code of the check")
    extra: dict | None = Field(default=None, description="Source-specific extra details (e.g. social-analyzer's match rate/title)")

    model_config = ConfigDict(from_attributes=True)


class SearchRunSummary(BaseModel):
    """Summary of a past or in-progress search run, without full site results"""

    id: int = Field(..., description="Search run ID")
    username: str = Field(..., description="Username that was searched")
    source: str = Field(..., description="Which search tool produced this run: maigret or social_analyzer")
    status: str = Field(..., description="running, completed, cancelled, or failed")
    total_sites_checked: int = Field(..., description="Number of sites checked")
    found_count: int = Field(..., description="Number of sites where the username was found")
    error_message: str | None = Field(default=None, description="Error message if the run failed")
    tags: list[str] | None = Field(default=None, description="Tags the search was filtered to, if any")
    started_at: datetime.datetime = Field(..., description="When the search started")
    completed_at: datetime.datetime | None = Field(default=None, description="When the search completed")

    model_config = ConfigDict(from_attributes=True)


class SearchRunDetail(SearchRunSummary):
    """Full detail of a search run, including its found-site results"""

    site_results: list[SiteResultSchema] = Field(default_factory=list, description="Found sites")
    has_export: bool = Field(default=False, description="Whether a full report is available for export")


class UsernameSearchInfo(BaseModel):
    """Info about the underlying search tool and its site database"""

    tool: str = Field(..., description="Name of the underlying search tool")
    version: str = Field(..., description="Installed version of the search tool")
    site_count: int = Field(..., description="Number of sites in the currently loaded database")
    db_last_updated_at: datetime.datetime | None = Field(default=None, description="When the site database was last checked/refreshed")
    latest_version: str | None = Field(default=None, description="Latest version published on PyPI, if checked (social-analyzer only)")
    update_available: bool | None = Field(default=None, description="Whether a newer version is available on PyPI (social-analyzer only)")
