import datetime
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, StringConstraints, field_validator


def _clean_username(value: str) -> str:
    username = value.strip()
    if not username:
        raise ValueError("Username cannot be empty")
    return username


def _clean_label(value: str | None) -> str | None:
    return (value.strip() or None) if value is not None else None


class ScanRequest(BaseModel):
    """Request to start a new username search"""

    username: str = Field(..., description="Username to search for", min_length=1, max_length=100)
    source: Literal["maigret", "social_analyzer", "threat_actor_usernames"] = Field(
        default="maigret", description="Which search tool to use"
    )
    tags: list[str] | None = Field(
        default=None, description="Only scan sites with at least one of these tags (maigret only)"
    )
    excluded_tags: list[str] | None = Field(
        default=None, description="Skip sites with any of these tags (maigret only)"
    )
    parent_search_id: int | None = Field(
        default=None, ge=1, description="Run whose pivot this search follows, if any"
    )
    pivot_source: str | None = Field(
        default=None,
        max_length=200,
        description="Label for the pivot this search follows (stored as untrusted text)",
    )

    strip_username = field_validator("username")(_clean_username)
    strip_pivot_source = field_validator("pivot_source")(_clean_label)


class SiteCheckRequest(BaseModel):
    """Request to check one username on a few named sites only (confirming a pivot)"""

    username: str = Field(..., description="Username to check", min_length=1, max_length=100)
    site_names: list[Annotated[str, StringConstraints(min_length=1, max_length=100)]] = Field(
        ..., min_length=1, max_length=5, description="Maigret site names to check"
    )
    parent_search_id: int | None = Field(
        default=None, ge=1, description="Run whose pivot this check follows, if any"
    )
    pivot_source: str | None = Field(
        default=None,
        max_length=200,
        description="Label for the pivot this check follows (stored as untrusted text)",
    )

    strip_username = field_validator("username")(_clean_username)
    strip_pivot_source = field_validator("pivot_source")(_clean_label)


class SiteResultSchema(BaseModel):
    """A single claimed/found site result"""

    site_name: str = Field(..., description="Name of the site where the username was found")
    url_user: str = Field(..., description="URL of the found profile")
    http_status: int | None = Field(default=None, description="HTTP status code of the check")
    extra: dict | None = Field(
        default=None,
        description="Source-specific extra details (e.g. social-analyzer's match rate/title)",
    )

    model_config = ConfigDict(from_attributes=True)


class SearchRunSummary(BaseModel):
    """Summary of a past or in-progress search run, without full site results"""

    id: int = Field(..., description="Search run ID")
    username: str = Field(..., description="Username that was searched")
    source: str = Field(
        ...,
        description=(
            "Which search tool produced this run: maigret, social_analyzer, or "
            "threat_actor_usernames"
        ),
    )
    status: str = Field(..., description="running, completed, cancelled, or failed")
    total_sites_checked: int = Field(..., description="Number of sites checked")
    found_count: int = Field(..., description="Number of sites where the username was found")
    error_message: str | None = Field(default=None, description="Error message if the run failed")
    tags: list[str] | None = Field(
        default=None, description="Tags the search was filtered to, if any"
    )
    parent_search_id: int | None = Field(
        default=None,
        description="Run this one followed a pivot from (may no longer exist)",
    )
    pivot_source: str | None = Field(default=None, description="Label of the followed pivot")
    site_statuses: dict[str, str] | None = Field(
        default=None,
        description=(
            "Site checks only: site name -> Maigret verdict (claimed, available, unknown, "
            "illegal); null for a full scan"
        ),
    )
    started_at: datetime.datetime = Field(..., description="When the search started")
    completed_at: datetime.datetime | None = Field(
        default=None, description="When the search completed"
    )

    model_config = ConfigDict(from_attributes=True)


class PivotUsername(BaseModel):
    """Another handle or account ID found on a profile, to search next"""

    value: str = Field(..., description="The handle or account ID")
    kind: Literal["reported", "link"] = Field(
        ...,
        description=(
            "reported: the profile page itself named this account; link: a URL the profile "
            "owner typed in, resolved to the account it points at"
        ),
    )
    id_type: str = Field(
        ..., description="'username' for a plain handle, else the platform ID type (vk_id, ...)"
    )
    searchable: bool = Field(
        ..., description="Whether a username search for this value makes sense (plain handles)"
    )
    site: str | None = Field(
        default=None, description="Site a link-derived handle lives on, by Maigret site name"
    )
    sites: list[str] = Field(
        default_factory=list, description="Found sites whose profile exposed this value"
    )


class PivotName(BaseModel):
    """A display name found on a profile"""

    value: str = Field(..., description="The name as written")
    sites: list[str] = Field(default_factory=list, description="Found sites that showed it")


class PivotEmail(BaseModel):
    """An email address a profile published in one of its own fields"""

    value: str = Field(..., description="Lower-cased address")
    sites: list[str] = Field(default_factory=list, description="Found sites that showed it")


class RunPivots(BaseModel):
    """Leads harvested from a run's found profiles - hypotheses, not attribution"""

    usernames: list[PivotUsername] = Field(default_factory=list)
    names: list[PivotName] = Field(default_factory=list)
    emails: list[PivotEmail] = Field(default_factory=list)


class SearchRunDetail(SearchRunSummary):
    """Full detail of a search run, including its found-site results"""

    site_results: list[SiteResultSchema] = Field(default_factory=list, description="Found sites")
    has_export: bool = Field(
        default=False, description="Whether a full report is available for export"
    )
    pivots: RunPivots = Field(
        default_factory=RunPivots, description="Other handles, names and emails to pivot on"
    )
    parent_exists: bool = Field(
        default=False, description="Whether the run in `parent_search_id` still exists"
    )


class HudsonRockStealerSummary(BaseModel):
    """One infostealer infection linked to a username, per Hudson Rock's public API"""

    date_compromised: str | None = Field(
        default=None, description="When the infected computer's data was harvested"
    )
    computer_name: str | None = Field(
        default=None, description="Name of the infected computer, if known"
    )
    operating_system: str | None = Field(
        default=None, description="OS of the infected computer, if known"
    )


class HudsonRockCheckResponse(BaseModel):
    """Result of checking a username against Hudson Rock's free infostealer-exposure API"""

    username: str = Field(..., description="Username that was checked")
    stealers: list[HudsonRockStealerSummary] = Field(
        default_factory=list, description="Infostealer infections linked to this username"
    )


class UsernameSearchInfo(BaseModel):
    """Info about the underlying search tool and its site database"""

    tool: str = Field(..., description="Name of the underlying search tool")
    version: str = Field(..., description="Installed version of the search tool")
    site_count: int = Field(..., description="Number of sites in the currently loaded database")
    db_last_updated_at: datetime.datetime | None = Field(
        default=None, description="When the site database was last checked/refreshed"
    )
    latest_version: str | None = Field(
        default=None,
        description="Latest version published on PyPI, if checked (social-analyzer only)",
    )
    update_available: bool | None = Field(
        default=None,
        description="Whether a newer version is available on PyPI (social-analyzer only)",
    )
