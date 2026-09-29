import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.features.steam_recon.config.steam_recon_config import MAX_FRIENDS_CAP, MAX_FRIENDS_DEFAULT

Visibility = Literal["public", "friends_only", "private", "unknown"]
Confidence = Literal["high", "medium", "low"]
ScanStatus = Literal["running", "completed", "cancelled", "failed"]


class ProfileRequest(BaseModel):
    """Request for a quick Steam profile lookup."""

    target: str = Field(
        ...,
        min_length=1,
        max_length=512,
        description="SteamID64/3/2, a steamcommunity.com profile URL, or a vanity name",
    )

    @field_validator("target")
    @classmethod
    def strip_target(cls, v: str) -> str:
        stripped = v.strip()
        if not stripped:
            raise ValueError("Target cannot be empty")
        return stripped


class QuickLink(BaseModel):
    id: str
    label: str
    url: str


class SteamLocation(BaseModel):
    """A profile's self-declared location - Steam's codes plus best-effort resolved names."""

    country_code: str | None = None
    state_code: str | None = None
    city_id: int | None = None
    country: str | None = None
    state: str | None = None
    city: str | None = None


class SteamBans(BaseModel):
    community_banned: bool
    vac_banned: bool
    number_of_vac_bans: int
    days_since_last_ban: int
    number_of_game_bans: int
    economy_ban: str


class SteamProfile(BaseModel):
    steamid64: str
    persona_name: str | None = None
    real_name: str | None = None
    profile_url: str | None = None
    avatar_url: str | None = None
    visibility: Visibility = "unknown"
    created_at: int | None = Field(
        None, description="Account creation time, epoch seconds (public profiles only)"
    )
    last_logoff: int | None = Field(None, description="Epoch seconds")
    location: SteamLocation | None = None
    level: int | None = None
    game_count: int | None = Field(None, description="None when the game library is private")
    bans: SteamBans | None = None


class ProfileResponse(BaseModel):
    profile: SteamProfile
    quick_links: list[QuickLink]


# --- Scan ------------------------------------------------------------------------------------


class ScanRequest(BaseModel):
    """Request to start a Steam Recon scan: friends graph, close friends, geolocation, and
    optionally the CS2 cheater-probability report."""

    target: str = Field(..., min_length=1, max_length=512)
    max_friends: int = Field(
        default=MAX_FRIENDS_DEFAULT,
        ge=1,
        le=MAX_FRIENDS_CAP,
        description="How many of the target's public friends to analyze, oldest-connection first",
    )
    include_cs_report: bool = Field(
        default=True, description="Whether to compute the CS2 cheater-probability report"
    )

    @field_validator("target")
    @classmethod
    def strip_target(cls, v: str) -> str:
        stripped = v.strip()
        if not stripped:
            raise ValueError("Target cannot be empty")
        return stripped


class CloseFriend(BaseModel):
    """One entry in the close-friends ranking (mutual-connection weight, not just a friends-list
    entry - see docs/architecture/steam-recon.md)."""

    steamid64: str
    persona_name: str | None = None
    avatar_url: str | None = None
    mutual_count: int
    friend_since: int | None = Field(None, description="Epoch seconds")
    location: SteamLocation | None = None
    vac_banned: bool = False
    game_banned: bool = False
    friends_private: bool = False


class LocationCandidateSchema(BaseModel):
    code: str
    name: str | None = None
    weight: float
    share: float


class GeolocationHypothesis(BaseModel):
    """Probable location derived from the weighted social-graph vote - a hypothesis, not a
    fact. `self_declared` is the target's own profile location for comparison, when public."""

    confidence: Confidence
    num_voters: int
    coverage: float = Field(..., description="Fraction of connected friends with a usable location")
    countries: list[LocationCandidateSchema]
    states: list[LocationCandidateSchema]
    cities: list[LocationCandidateSchema]
    self_declared: SteamLocation | None = None


class CheaterSignal(BaseModel):
    id: str
    value: float | None = Field(None, description="0-1, or null when there was no usable data")
    weight: float
    contribution: float
    explanation: str


class CheaterReport(BaseModel):
    """CS2 cheater-probability heuristic - a transparent weighted-signal estimate, not a
    verdict. See docs/adr/0014-steam-recon-clean-room-and-heuristic-scoring.md."""

    probability: float
    level: Literal["low", "medium", "high"]
    coverage: float = Field(..., description="Fraction of the 5 signals that had usable data")
    already_banned: bool
    signals: list[CheaterSignal]


class ScanResult(BaseModel):
    """Full scan result blob, persisted as-is and returned by both the SSE `completed` event's
    follow-up fetch and the history detail endpoint."""

    profile: SteamProfile
    quick_links: list[QuickLink]
    close_friends: list[CloseFriend]
    geolocation: GeolocationHypothesis
    cheater_report: CheaterReport | None = None


class SearchSummary(BaseModel):
    id: int
    target: str
    steamid64: str | None = None
    persona_name: str | None = None
    status: ScanStatus
    error_message: str | None = None
    max_friends: int
    include_cs_report: bool
    friends_total: int
    friends_analyzed: int
    friends_located: int
    top_country_code: str | None = None
    cheater_probability: float | None = None
    started_at: datetime.datetime
    completed_at: datetime.datetime | None = None

    model_config = ConfigDict(from_attributes=True)


class SearchDetail(SearchSummary):
    result: ScanResult | None = None
