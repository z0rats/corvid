import datetime
import re
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

_EMAIL = re.compile(r"[^@\s]+@[^@\s]+\.[^@\s]{2,}")


class ScanRequest(BaseModel):
    """Request to start a new email search"""

    username: str = Field(
        ...,
        description=(
            "mailcat: username (or the local part of an email) to probe at mail providers. "
            "user_scanner: the full email address to look up"
        ),
        min_length=1,
        max_length=100,
    )
    source: Literal["mailcat", "user_scanner"] = Field(
        default="mailcat", description="Which search tool to use"
    )

    @model_validator(mode="after")
    def normalize_target(self) -> ScanRequest:
        target = self.username.strip()
        if not target:
            raise ValueError("Username cannot be empty")
        if self.source == "user_scanner":
            if not _EMAIL.fullmatch(target):
                raise ValueError("user_scanner needs a full email address")
            self.username = target
        else:
            self.username = target.split("@")[0] if "@" in target else target
        return self


class ProviderResultSchema(BaseModel):
    """A single provider where the searched username was found registered"""

    provider_name: str = Field(
        ..., description="Name of the mail provider where the username was found"
    )
    emails: list[str] = Field(..., description="Email address(es) found at this provider")
    extra: dict | None = Field(default=None, description="Provider-specific extra details")

    model_config = ConfigDict(from_attributes=True)


class SearchRunSummary(BaseModel):
    """Summary of a past or in-progress search run, without full provider results"""

    id: int = Field(..., description="Search run ID")
    username: str = Field(..., description="Username or email address that was searched")
    source: str = Field(
        ..., description="Which search tool produced the run: mailcat or user_scanner"
    )
    status: str = Field(..., description="running, completed, cancelled, or failed")
    total_providers_checked: int = Field(..., description="Number of providers checked")
    found_count: int = Field(
        ..., description="Number of providers where the username was found registered"
    )
    error_count: int = Field(
        default=0,
        description="user_scanner only: checks that failed rather than answered",
    )
    error_message: str | None = Field(default=None, description="Error message if the run failed")
    started_at: datetime.datetime = Field(..., description="When the search started")
    completed_at: datetime.datetime | None = Field(
        default=None, description="When the search completed"
    )

    model_config = ConfigDict(from_attributes=True)


class SearchRunDetail(SearchRunSummary):
    """Full detail of a search run, including its found-provider results"""

    provider_results: list[ProviderResultSchema] = Field(
        default_factory=list, description="Found providers"
    )


class EmailSearchInfo(BaseModel):
    """Info about the underlying mailcat tool and its installed/available version"""

    tool: str = Field(..., description="Name of the underlying search tool")
    version: str = Field(..., description="Installed version of the search tool")
    provider_count: int = Field(
        ..., description="Number of provider checkers currently active, given the current settings"
    )
    available: bool = Field(
        default=True, description="False when the tool's package isn't installed in this image"
    )
    blocked_reason: str | None = Field(
        default=None,
        description="Why a scan with this tool would be refused under the current settings",
    )
    latest_version: str | None = Field(
        default=None, description="Latest version published on PyPI, if checked"
    )
    update_available: bool | None = Field(
        default=None, description="Whether a newer version is available on PyPI"
    )
