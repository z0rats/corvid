import datetime
import re
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator

# Deliberately not `EmailStr` (pydantic[email]) - minimizing dependencies for a "does this look
# like an email" check, same reasoning as the codebase's other feature-level email validators.
_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


class GhuntProfileRequest(BaseModel):
    """Request to look up a Google account profile by email"""

    email: str = Field(..., min_length=3, max_length=254, description="Email address to look up")

    @field_validator("email")
    @classmethod
    def validate_email(cls, v: str) -> str:
        email = v.strip()
        if not _EMAIL_RE.match(email):
            raise ValueError("Not a valid email address")
        return email


class GhuntSessionSaveRequest(BaseModel):
    """Request to store a new GHunt session (the raw base64 content of `creds.m`)"""

    value: str = Field(..., min_length=1, description="Base64 content of GHunt's creds.m")


class GhuntPhoto(BaseModel):
    """A profile or cover photo, as GHunt's PersonPhoto object reports it"""

    url: str | None = Field(default=None, description="Photo URL")
    is_default: bool = Field(default=False, description="Whether this is Google's default photo")

    model_config = ConfigDict(from_attributes=True)


class GhuntProfileResponse(BaseModel):
    """A Google account's public profile data, as returned by `ghunt email <address> --json`.

    Only the stable `profile` (GHunt's `Person` object) section is fully modeled here - `emails`/
    `profilePhotos`/etc. are keyed by container in GHunt's own output, but only the "PROFILE"
    container is ever populated for a plain email lookup, so that key is flattened away here.
    `play_games`/`maps`/`calendar` are large, partly-dead nested objects upstream (e.g. Maps
    reviews/photos are currently disabled server-side in GHunt itself, leaving only aggregate
    `stats`) - round-tripped as opaque JSON rather than fully typed until a real captured fixture
    justifies deepening them (see docs/architecture/ghunt.md).
    """

    gaia_id: str = Field(..., description="Google's internal account identifier (personId)")
    email: str = Field(..., description="The looked-up email address")
    # GHunt's own name-scraping is a permanent no-op upstream (Google patched it away), so this
    # is always empty - see docs/architecture/ghunt.md. Kept out of the response entirely rather
    # than exposing a field that can never be populated.
    profile_photo: GhuntPhoto | None = Field(default=None, description="Profile picture")
    cover_photo: GhuntPhoto | None = Field(default=None, description="Cover picture")
    last_profile_edit: datetime.datetime | None = Field(
        default=None, description="When the profile was last edited, if known"
    )
    user_types: list[str] = Field(default_factory=list, description="Google account user types")
    activated_services: list[str] = Field(
        default_factory=list, description="Google services activated on this account"
    )
    entity_type: str | None = Field(default=None, description="Google Chat entity type")
    is_enterprise_user: bool = Field(
        default=False, description="Whether this is a Google Workspace (enterprise) account"
    )
    play_games: dict[str, Any] | None = Field(
        default=None, description="Raw Play Games data, if a public profile was found"
    )
    maps: dict[str, Any] | None = Field(default=None, description="Raw Google Maps statistics")
    calendar: dict[str, Any] | None = Field(
        default=None, description="Raw public Google Calendar data, if any"
    )


class GhuntHealthResponse(BaseModel):
    """Whether the GHunt CLI is installed, its version, and whether a session is configured"""

    installed: bool = Field(..., description="Whether the GHunt binary is available")
    version: str | None = Field(default=None, description="Installed GHunt version")
    latest_version: str | None = Field(
        default=None, description="Latest version published on PyPI, best-effort"
    )
    session_configured: bool = Field(
        ..., description="Whether an active, structurally valid GHunt session is stored"
    )
