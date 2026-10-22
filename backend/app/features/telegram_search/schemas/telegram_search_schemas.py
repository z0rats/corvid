import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.features.telegram_search.config.telegram_search_config import (
    MAX_POSTS_CAP,
    MAX_POSTS_DEFAULT,
)
from app.features.telegram_search.utils.channel_name import normalize_channel

ScanStatus = Literal["running", "completed", "cancelled", "failed"]
ChannelKind = Literal["channel", "group", "unknown"]


class ScanRequest(BaseModel):
    target: str = Field(
        ...,
        min_length=1,
        max_length=200,
        description="@username, username, or a t.me / t.me/s link of a public channel or group",
    )
    max_posts: int = Field(
        MAX_POSTS_DEFAULT,
        ge=1,
        le=MAX_POSTS_CAP,
        description="How many of the newest posts to sample from the channel's web preview",
    )

    @field_validator("target")
    @classmethod
    def validate_target(cls, v: str) -> str:
        normalize_channel(v)
        return v.strip()

    @property
    def channel(self) -> str:
        return normalize_channel(self.target)


class ChannelProfile(BaseModel):
    username: str
    url: str
    title: str
    kind: ChannelKind
    member_count: int | None = Field(None, description="Subscribers (channel) or members (group)")
    online_count: int | None = Field(None, description="Members online now (groups only)")
    description: str | None = None
    verified: bool = False
    photo_url: str | None = None
    created_at: datetime.datetime | None = Field(
        None, description="Date of the channel's first post ('Channel created'), when reachable"
    )
    preview_available: bool = Field(
        ...,
        description="Whether Telegram serves the t.me/s message preview - false for groups and "
        "for channels that turned it off, so no post metrics",
    )
    media_counters: dict[str, int] = Field(
        default_factory=dict,
        description="Preview header totals (photos, videos, files, links); Telegram rounds them",
    )


class ForwardSourceStat(BaseModel):
    name: str | None = Field(None, description="Display name; null when the sender hid it")
    username: str | None = Field(None, description="Set only for a public channel source")
    count: int


class MentionStat(BaseModel):
    username: str
    count: int


class SampledPost(BaseModel):
    id: int
    url: str
    date: datetime.datetime | None = None
    views: int | None = None
    text: str = ""
    forwarded_from: ForwardSourceStat | None = None
    has_media: bool = False
    link_count: int = 0


class ChannelMetrics(BaseModel):
    posts_sampled: int
    first_sampled_at: datetime.datetime | None = None
    last_post_at: datetime.datetime | None = None
    posts_per_day: float | None = Field(None, description="Over the sampled date range")
    avg_views: int | None = None
    median_views: int | None = None
    max_views: int | None = None
    views_to_members: float | None = Field(
        None, description="Average views / subscribers - a rough reach (or view-inflation) signal"
    )
    forwarded_count: int = 0
    forwarded_ratio: float | None = None
    media_ratio: float | None = None
    top_forward_sources: list[ForwardSourceStat] = Field(default_factory=list)
    top_mentions: list[MentionStat] = Field(default_factory=list)


class ScanResult(BaseModel):
    """Full result blob, persisted as-is and returned by the history detail endpoint."""

    profile: ChannelProfile
    metrics: ChannelMetrics | None = None
    top_posts: list[SampledPost] = Field(default_factory=list)
    posts: list[SampledPost] = Field(
        default_factory=list, description="Sampled posts, newest first"
    )
    indicators: dict[str, list[str]] = Field(
        default_factory=dict,
        description="IOCs from sampled posts and the description: urls, domains, ips, emails, "
        "cves, md5, sha1, sha256 (Telegram's own links excluded)",
    )


class SearchSummary(BaseModel):
    id: int
    target: str
    channel: str
    title: str | None = None
    kind: str | None = None
    member_count: int | None = None
    status: ScanStatus
    error_message: str | None = None
    max_posts: int
    posts_sampled: int
    started_at: datetime.datetime
    completed_at: datetime.datetime | None = None

    model_config = ConfigDict(from_attributes=True)


class SearchDetail(SearchSummary):
    result: ScanResult | None = None
