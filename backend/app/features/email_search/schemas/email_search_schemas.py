import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator


class ScanRequest(BaseModel):
    """Request to start a new email search"""

    username: str = Field(..., description="Username (or local-part of an email) to search for", min_length=1, max_length=100)

    @field_validator("username")
    @classmethod
    def validate_username(cls, v: str) -> str:
        username = v.strip()
        if not username:
            raise ValueError("Username cannot be empty")
        return username.split("@")[0] if "@" in username else username


class ProviderResultSchema(BaseModel):
    """A single provider where the searched username was found registered"""

    provider_name: str = Field(..., description="Name of the mail provider where the username was found")
    emails: list[str] = Field(..., description="Email address(es) found at this provider")
    extra: dict | None = Field(default=None, description="Provider-specific extra details")

    model_config = ConfigDict(from_attributes=True)


class SearchRunSummary(BaseModel):
    """Summary of a past or in-progress search run, without full provider results"""

    id: int = Field(..., description="Search run ID")
    username: str = Field(..., description="Username that was searched")
    status: str = Field(..., description="running, completed, cancelled, or failed")
    total_providers_checked: int = Field(..., description="Number of providers checked")
    found_count: int = Field(..., description="Number of providers where the username was found registered")
    error_message: str | None = Field(default=None, description="Error message if the run failed")
    started_at: datetime.datetime = Field(..., description="When the search started")
    completed_at: datetime.datetime | None = Field(default=None, description="When the search completed")

    model_config = ConfigDict(from_attributes=True)


class SearchRunDetail(SearchRunSummary):
    """Full detail of a search run, including its found-provider results"""

    provider_results: list[ProviderResultSchema] = Field(default_factory=list, description="Found providers")


class EmailSearchInfo(BaseModel):
    """Info about the underlying mailcat tool and its installed/available version"""

    tool: str = Field(..., description="Name of the underlying search tool")
    version: str = Field(..., description="Installed version of the search tool")
    provider_count: int = Field(..., description="Number of provider checkers currently active, given the current settings")
    latest_version: str | None = Field(default=None, description="Latest version published on PyPI, if checked")
    update_available: bool | None = Field(default=None, description="Whether a newer version is available on PyPI")
