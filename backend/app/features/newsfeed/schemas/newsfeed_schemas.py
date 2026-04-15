import datetime
from typing import Any, Literal

from pydantic import AnyHttpUrl, BaseModel, ConfigDict, Field

IocType = Literal["ips", "md5_hashes", "sha1_hashes", "sha256_hashes", "urls", "domains", "emails"]
BlacklistType = Literal["word", "ioc"]


class NewsfeedSettingsSchema(BaseModel):
    name: str = Field(..., description="Display name for the news feed")
    url: AnyHttpUrl = Field(..., description="RSS feed URL")
    icon: str = Field(default="default.png", description="Feed icon filename")
    icon_id: str | None = Field(default=None, description="Unique icon identifier")
    enabled: bool = Field(default=True, description="Whether the feed is active")

    model_config = ConfigDict(from_attributes=True)


class NewsfeedSettingsCreateSchema(BaseModel):
    name: str = Field(..., description="Display name for the news feed")
    url: AnyHttpUrl = Field(..., description="RSS feed URL")
    enabled: bool = Field(default=True, description="Whether the feed is active")


class NewsArticleSchema(BaseModel):
    id: int | None = Field(default=None, description="Unique article identifier")
    feedname: str = Field(..., description="Name of the source feed")
    icon: str = Field(..., description="Feed icon filename")
    title: str = Field(..., description="Article title")
    summary: str = Field(..., description="Article summary or description")
    full_text: str | None = Field(default='', description="Full article body text")
    date: datetime.datetime = Field(..., description="Publication date of the article")
    link: str = Field(..., description="URL to the original article")
    fetched_at: datetime.datetime = Field(..., description="Timestamp when the article was fetched")
    matches: list[str] | None = Field(default=None, description="Keyword matches found in the article")
    iocs: dict[str, list[str]] | None = Field(default=None, description="Extracted indicators of compromise")
    relevant_iocs: list[str] | None = Field(default=None, description="IOCs flagged as relevant")
    analysis_result: str | None = Field(default=None, description="LLM analysis result for this article")
    note: str | None = Field(default=None, description="Analyst note attached to this article")
    tlp: str | None = Field(default="TLP:CLEAR", description="Traffic Light Protocol classification")
    read: bool = Field(default=False, description="Whether the article has been marked as read")

    model_config = ConfigDict(from_attributes=True)


class NewsfeedConfigSchema(BaseModel):
    id: int = Field(..., description="Configuration record ID")
    retention_days: int = Field(..., description="Number of days to retain articles")
    background_fetch_enabled: bool = Field(..., description="Whether background feed fetching is active")
    fetch_interval_minutes: int = Field(..., description="Interval between feed fetches in minutes")
    last_fetch_timestamp: datetime.datetime | None = Field(default=None, description="Timestamp of the last feed fetch")
    keyword_matching_enabled: bool = Field(default=False, description="Whether keyword matching is enabled")

    model_config = ConfigDict(from_attributes=True)


class NewsfeedConfigUpdateSchema(BaseModel):
    retention_days: int | None = Field(default=None, description="Number of days to retain articles")
    background_fetch_enabled: bool | None = Field(default=None, description="Whether background feed fetching is active")
    fetch_interval_minutes: int | None = Field(default=None, description="Interval between feed fetches in minutes")
    keyword_matching_enabled: bool | None = Field(default=None, description="Whether keyword matching is enabled")


class UpdateArticleRequest(BaseModel):
    note: str | None = Field(default=None, description="Analyst note for the article")
    tlp: str | None = Field(default=None, description="TLP classification (e.g. TLP:CLEAR, TLP:GREEN)")
    read: bool | None = Field(default=None, description="Whether the article has been read")


class NewsAnalysisParams(BaseModel):
    """Parameters for customizing news article analysis"""
    model_id: str | None = Field(default=None, description="Model ID to use for analysis (null = use configured default)")
    temperature: float = Field(default=0.3, ge=0.0, le=1.0, description="Temperature for generation (0.0-1.0)")
    max_tokens: int = Field(default=2000, ge=1, description="Maximum tokens for response")
    analyze_bias: bool = Field(default=True, description="Include bias assessment")
    analyze_missing_perspectives: bool = Field(default=True, description="Include missing perspectives")
    custom_focus: list[str] | None = Field(default=None, description="Custom analysis focus areas")


class ArticleAnalysisRequest(BaseModel):
    """Request body for LLM-based article analysis"""
    model_id: str | None = Field(default=None, description="LLM model ID to use for analysis (null = use configured default)")
    temperature: float = Field(default=0.3, ge=0.0, le=1.0, description="Temperature for generation (0.0–1.0)")
    max_tokens: int = Field(default=2000, ge=1, description="Maximum tokens in the response")
    use_cti_settings: bool = Field(default=True, description="Apply CTI profile settings to the analysis")
    force: bool = Field(default=False, description="Force re-analysis even if a result already exists")


class AnalysisResultResponse(BaseModel):
    """Response for article analysis"""
    message: str = Field(..., description="Status message for the analysis operation")
    analysis_result: dict[str, Any] = Field(..., description="LLM analysis output")
    cti_settings_used: bool | None = Field(default=None, description="Whether CTI profile settings were applied")


class FeedInfo(BaseModel):
    """Parsed information from a validated RSS/Atom feed"""
    title: str = Field(default="", description="Feed title")
    description: str = Field(default="", description="Feed description")
    version: str = Field(default="", description="Feed format version (e.g. RSS 2.0, Atom 1.0)")
    entry_count: int = Field(default=0, description="Number of entries in the feed")


class FeedValidationResponse(BaseModel):
    """Response for feed URL validation"""
    valid: bool = Field(..., description="Whether the feed URL is valid and parseable")
    feed_info: FeedInfo | None = Field(default=None, description="Parsed feed metadata if valid")


class IconUploadResponse(BaseModel):
    """Response for icon upload"""
    message: str = Field(..., description="Upload status message")
    icon_id: str = Field(..., description="Generated icon identifier")


class IocEntry(BaseModel):
    """A single IOC frequency entry"""
    value: str = Field(..., description="IOC value")
    count: int = Field(..., description="Number of occurrences")
    article_ids: list[int] = Field(default_factory=list, description="IDs of articles containing this IOC")


class CveEntry(BaseModel):
    """A single CVE frequency entry"""
    value: str = Field(..., description="CVE identifier")
    count: int = Field(..., description="Number of occurrences")
    article_ids: list[int] = Field(default_factory=list, description="IDs of articles mentioning this CVE")


class WordFrequencyEntry(BaseModel):
    """A single word frequency entry"""
    word: str = Field(..., description="Word or term")
    count: int = Field(..., description="Number of occurrences")
    article_ids: list[int] = Field(default_factory=list, description="IDs of articles containing this word")


class IocDistributionEntry(BaseModel):
    """IOC type distribution entry for chart consumption"""
    id: str = Field(..., description="IOC type identifier")
    label: str = Field(..., description="Human-readable IOC type label")
    value: int = Field(..., description="Count of IOCs of this type")


class MessageResponse(BaseModel):
    """Simple message response"""
    message: str = Field(..., description="Response message")


class ArticleAnalysisResult(BaseModel):
    """Single ranked and analyzed article result"""
    article_id: int = Field(..., description="ID of the analyzed article")
    title: str = Field(default="", description="Article title")
    relevance_score: int = Field(default=99, description="Relevance score (lower is more relevant)")
    reason_for_ranking: str = Field(default="", description="Explanation for the relevance ranking")
    analysis: dict[str, Any] = Field(..., description="Detailed analysis output")


class ArticleAnalysisResponse(BaseModel):
    """Response for article analysis results"""
    articles_analysis: list[ArticleAnalysisResult] = Field(..., description="List of analyzed articles")


class RecentArticleSchema(BaseModel):
    """Lightweight article summary used in headline/trend views"""
    id: int = Field(..., description="Article ID")
    title: str = Field(..., description="Article title")
    feedname: str = Field(..., description="Source feed name")
    date: datetime.datetime = Field(..., description="Publication date")


class PaginatedArticlesResponse(BaseModel):
    """Paginated response wrapping a list of full news articles"""
    total_count: int = Field(..., description="Total number of matching articles")
    page: int = Field(..., description="Current page number")
    page_size: int = Field(..., description="Number of articles per page")
    articles: list[NewsArticleSchema] = Field(..., description="Articles on this page")


class ArticleIocsResponse(BaseModel):
    """Extracted IOCs from a news article"""
    ips: list[str] = Field(default_factory=list, description="IP addresses")
    md5_hashes: list[str] = Field(default_factory=list, description="MD5 hashes")
    sha1_hashes: list[str] = Field(default_factory=list, description="SHA1 hashes")
    sha256_hashes: list[str] = Field(default_factory=list, description="SHA256 hashes")
    urls: list[str] = Field(default_factory=list, description="URLs")
    domains: list[str] = Field(default_factory=list, description="Domain names")
    emails: list[str] = Field(default_factory=list, description="Email addresses")
    cves: list[str] = Field(default_factory=list, description="CVE identifiers")


class BulkArticleRequest(BaseModel):
    """Request body for bulk article fetch with size constraint"""
    article_ids: list[int] = Field(..., description="List of article IDs", min_length=1, max_length=200)


class FeedStatusUpdate(BaseModel):
    """Request body for toggling a feed's enabled status"""
    enabled: bool = Field(..., description="Whether the feed should be enabled")


class RetentionDaysUpdate(BaseModel):
    """Request body for updating the article retention period"""
    retention_days: int = Field(..., ge=0, description="Number of days to retain articles (0 = unlimited)")


class RetentionDaysResponse(BaseModel):
    """Response for retention days update"""
    message: str = Field(..., description="Status message")
    retention_days: int = Field(..., description="Updated retention period in days")


class IconRefetchResponse(BaseModel):
    """Response for single feed favicon refetch"""
    success: bool = Field(..., description="Whether the favicon was successfully downloaded")
    message: str = Field(..., description="Status message")
    feed_name: str = Field(..., description="Name of the feed")
    icon_id: str | None = Field(default=None, description="New icon identifier if successful")


class FeedIconRefetchResult(BaseModel):
    """Result for a single feed in bulk refetch"""
    feed_name: str = Field(..., description="Name of the feed")
    success: bool = Field(..., description="Whether favicon was downloaded")
    icon_id: str | None = Field(default=None, description="New icon identifier if successful")
    error: str | None = Field(default=None, description="Error message if failed")


class BulkIconRefetchResponse(BaseModel):
    """Response for bulk favicon refetch operation"""
    total: int = Field(..., description="Total feeds attempted")
    succeeded: int = Field(..., description="Number of successful downloads")
    failed: int = Field(..., description="Number of failed downloads")
    results: list[FeedIconRefetchResult] = Field(..., description="Per-feed results")


class BlacklistEntryCreate(BaseModel):
    """Request body for creating a trends blacklist entry"""
    value: str = Field(..., min_length=1, max_length=255, description="Value to blacklist (word or IOC)")
    type: BlacklistType = Field(..., description="Blacklist type: 'word' or 'ioc'")


class BlacklistEntryResponse(BaseModel):
    """Response for a trends blacklist entry"""
    id: int = Field(..., description="Unique identifier")
    value: str = Field(..., description="Blacklisted value")
    type: str = Field(..., description="Blacklist type: 'word' or 'ioc'")
    created_at: datetime.datetime = Field(..., description="When the entry was created")

    model_config = ConfigDict(from_attributes=True)


class BlacklistDeleteResponse(BaseModel):
    """Response for blacklist entry deletion"""
    detail: str = Field(..., description="Status message")
