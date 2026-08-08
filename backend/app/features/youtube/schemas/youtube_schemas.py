from typing import Literal

from pydantic import BaseModel, Field, field_validator

CommentOrder = Literal["relevance", "time"]


class YoutubeLookupRequest(BaseModel):
    """Request to look up metadata for a YouTube video URL."""

    url: str = Field(..., min_length=1, max_length=2048, description="YouTube video URL (watch/shorts/embed/youtu.be)")

    @field_validator("url")
    @classmethod
    def strip_url(cls, v: str) -> str:
        stripped = v.strip()
        if not stripped:
            raise ValueError("URL cannot be empty")
        return stripped


class YoutubeOembedData(BaseModel):
    """Keyless metadata from YouTube's public oEmbed endpoint."""

    title: str | None = None
    author_name: str | None = None
    author_url: str | None = None
    thumbnail_url: str | None = None
    html: str | None = None
    provider_name: str | None = None
    width: int | None = None
    height: int | None = None


class YoutubePageMetadata(BaseModel):
    """Best-effort enrichment scraped from the video page's meta/link tags
    (schema.org VideoObject itemprops + Open Graph) - not exposed by oEmbed."""

    description: str | None = None
    duration: str | None = None
    date_published: str | None = None
    upload_date: str | None = None
    genre: str | None = None
    channel_id: str | None = None
    keywords: str | None = None
    is_family_friendly: str | None = None
    interaction_count: str | None = None


class YoutubeApiData(BaseModel):
    """Extended metadata from the YouTube Data API v3, only populated when a key
    is configured under Settings > API Keys."""

    published_at: str | None = None
    channel_id: str | None = None
    channel_title: str | None = None
    description: str | None = None
    tags: list[str] = Field(default_factory=list)
    category_id: str | None = None
    duration: str | None = None
    definition: str | None = None
    view_count: str | None = None
    like_count: str | None = None
    comment_count: str | None = None
    privacy_status: str | None = None


class YoutubeLookupResponse(BaseModel):
    """Aggregated YouTube video metadata from all available tiers."""

    video_id: str
    video_url: str
    oembed: YoutubeOembedData
    page_metadata: YoutubePageMetadata | None = None
    thumbnails: dict[str, str] = Field(default_factory=dict)
    api_data: YoutubeApiData | None = None
    api_configured: bool = Field(default=False, description="Whether a YouTube Data API key is configured")


class YoutubeCommentsRequest(BaseModel):
    """Request to list or search a YouTube video's top-level comments."""

    url: str = Field(..., min_length=1, max_length=2048, description="YouTube video URL (watch/shorts/embed/youtu.be)")
    query: str | None = Field(
        default=None, max_length=200,
        description="Optional keyword to filter comments by (author or text), scanned server-side across multiple pages",
    )
    order: CommentOrder = "relevance"
    page_token: str | None = Field(default=None, max_length=2048)

    @field_validator("url")
    @classmethod
    def strip_url(cls, v: str) -> str:
        stripped = v.strip()
        if not stripped:
            raise ValueError("URL cannot be empty")
        return stripped

    @field_validator("query")
    @classmethod
    def strip_query(cls, v: str | None) -> str | None:
        if v is None:
            return None
        stripped = v.strip()
        return stripped or None


class YoutubeComment(BaseModel):
    """A single top-level YouTube comment."""

    comment_id: str
    author_display_name: str | None = None
    author_channel_url: str | None = None
    author_profile_image_url: str | None = None
    text: str = ""
    like_count: int = 0
    reply_count: int = 0
    published_at: str | None = None
    updated_at: str | None = None


class YoutubeCommentsResponse(BaseModel):
    """A page of top-level comments, or a set of keyword matches when `query` was given."""

    video_id: str
    comments: list[YoutubeComment] = Field(default_factory=list)
    next_page_token: str | None = None
    query: str | None = None
    truncated: bool = Field(
        default=False,
        description="For a keyword search: true when the page/result-count cap was hit before "
                     "the video's comments were exhausted, so there may be further matches on "
                     "the next page (see next_page_token)",
    )
    pages_scanned: int = Field(default=0, description="Upstream API pages fetched to build this response")
