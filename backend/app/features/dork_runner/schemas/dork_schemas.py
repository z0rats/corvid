from datetime import datetime, timezone
from typing import Literal

from pydantic import BaseModel, Field, field_validator

TargetType = Literal["domain", "username", "email"]
EngineName = Literal["duckduckgo", "google", "bing"]


class DorkRunRequest(BaseModel):
    """Request to run a set of dork templates against a target."""

    target: str = Field(..., min_length=1, max_length=255, description="Domain, username, or email to dork against")
    target_type: TargetType = Field(..., description="Type of the target, used to select applicable templates")
    engine: EngineName = Field(default="duckduckgo", description="Search engine to query")
    template_keys: list[str] | None = Field(
        default=None,
        description="Subset of template keys to run; omit to run all templates applicable to target_type",
    )

    @field_validator("target")
    @classmethod
    def strip_target(cls, v: str) -> str:
        stripped = v.strip()
        if not stripped:
            raise ValueError("Target cannot be empty")
        return stripped


class DorkResult(BaseModel):
    """A single search result from one dork query."""

    template_key: str = Field(..., description="Dork template that produced this result")
    query: str = Field(..., description="Fully substituted query string that was sent")
    title: str = Field(default="", description="Result title")
    url: str = Field(default="", description="Result URL")
    snippet: str = Field(default="", description="Result snippet/description")


class DorkRunResponse(BaseModel):
    """Aggregated results across all queries in a dork run."""

    target: str
    target_type: TargetType
    engine: EngineName
    results: list[DorkResult] = Field(default_factory=list)
    total_results: int = Field(default=0, ge=0)
    queries_run: int = Field(default=0, ge=0)
    errors: list[str] = Field(default_factory=list, description="Per-query failures (e.g. blocked/CAPTCHA'd), non-fatal")
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class DorkTemplateInfo(BaseModel):
    """A dork template, as exposed to the frontend for selection."""

    key: str
    pattern: str
    description: str
    target_types: list[str]
