import datetime
import uuid

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, JSON, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship, validates
from sqlalchemy.sql import func

from app.core.database import Base


def generate_icon_id() -> str:
    return str(uuid.uuid4())


class NewsfeedSettings(Base):
    __tablename__ = "newsfeed_settings"

    name: Mapped[str] = mapped_column(String(255), primary_key=True, comment="Unique feed name, natural key")
    url: Mapped[str] = mapped_column(String(2048), comment="RSS/Atom feed URL")
    icon: Mapped[str] = mapped_column(
        String(36), default='default.png',
        comment="'default.png' or <uuid4().hex>.png written by favicon_downloader.py - 36 chars covers both",
    )
    icon_id: Mapped[str] = mapped_column(
        String, default=generate_icon_id, comment="Cache-busting id appended to the icon URL on the frontend"
    )
    enabled: Mapped[bool] = mapped_column(default=True, comment="Whether this feed is actively fetched")
    deleted: Mapped[bool] = mapped_column(
        default=False, comment="Soft-delete flag; kept to avoid orphaning already-stored news_articles rows"
    )
    last_fetched_at: Mapped[datetime.datetime | None] = mapped_column(
        DateTime(timezone=True), comment="When this feed was last polled, regardless of outcome"
    )
    last_success_at: Mapped[datetime.datetime | None] = mapped_column(
        DateTime(timezone=True), comment="When this feed was last polled successfully"
    )
    last_error: Mapped[str | None] = mapped_column(String(500), comment="Error message from the last failed fetch, if any")

    articles: Mapped[list["NewsArticle"]] = relationship(back_populates="feed", passive_deletes=True)


class NewsArticle(Base):
    __tablename__ = 'news_articles'

    id: Mapped[int] = mapped_column(primary_key=True, comment="Surrogate primary key")
    feedname: Mapped[str] = mapped_column(
        String(255), ForeignKey("newsfeed_settings.name", ondelete="CASCADE"), index=True,
        comment="Owning feed's name (newsfeed_settings.name)",
    )
    icon: Mapped[str] = mapped_column(String(36), comment="Copy of the owning feed's icon filename at fetch time")
    title: Mapped[str] = mapped_column(String(500), comment="Article title")
    summary: Mapped[str] = mapped_column(
        Text, comment="RSS description/summary field - no length cap in feed_processing_service.py, "
                      "some feeds put substantial content here, so Text rather than a guessed VARCHAR(N)",
    )
    full_text: Mapped[str | None] = mapped_column(Text, comment="Full article body, if fetched")
    date: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), index=True, comment="Publication date as reported by the feed"
    )
    link: Mapped[str] = mapped_column(String(2048), unique=True, index=True, comment="Article URL, deduplication key")
    fetched_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.datetime.now(datetime.timezone.utc),
        comment="When this article was ingested by Corvid",
    )
    matches: Mapped[list[str] | None] = mapped_column(JSON, comment="Keyword-matching hits found in this article")
    iocs: Mapped[dict[str, list[str]] | None] = mapped_column(JSON, comment="IOCs extracted from the article, by type")
    relevant_iocs: Mapped[list[str] | None] = mapped_column(
        JSON, comment="Subset of iocs judged relevant to the configured CTI profile"
    )
    analysis_result: Mapped[str | None] = mapped_column(Text, comment="LLM-generated analysis of the article")
    mitre_attack: Mapped[str | None] = mapped_column(Text, comment="LLM-extracted MITRE ATT&CK technique mapping")
    note: Mapped[str | None] = mapped_column(Text, comment="User-entered free-text note")
    tlp: Mapped[str] = mapped_column(String, default="TLP:CLEAR", comment="Traffic Light Protocol label")
    read: Mapped[bool] = mapped_column(default=False, comment="Whether the user has marked this article as read")

    feed: Mapped["NewsfeedSettings"] = relationship(back_populates="articles")


class NewsfeedConfig(Base):
    __tablename__ = 'newsfeed_config'

    id: Mapped[int] = mapped_column(primary_key=True, comment="Singleton row id, always 1")
    retention_days: Mapped[int] = mapped_column(
        default=0, comment="Days to keep articles before pruning; 0 = keep forever"
    )
    background_fetch_enabled: Mapped[bool] = mapped_column(
        default=True, comment="Whether the scheduler job fetches feeds automatically"
    )
    fetch_interval_minutes: Mapped[int] = mapped_column(default=60, comment="Minutes between scheduled feed fetches")
    last_fetch_timestamp: Mapped[datetime.datetime | None] = mapped_column(
        DateTime(timezone=True), comment="When the background fetch job last ran, across all feeds"
    )
    keyword_matching_enabled: Mapped[bool] = mapped_column(
        default=False, comment="Whether articles are matched against the configured keyword list"
    )


class TrendsBlacklistEntry(Base):
    """Blacklisted words and IOC values excluded from trends analytics"""
    __tablename__ = 'trends_blacklist'
    __table_args__ = (
        UniqueConstraint('value', 'type', name='uq_blacklist_value_type'),
        CheckConstraint("type IN ('word', 'ioc')", name="ck_trends_blacklist_type"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, comment="Surrogate primary key")
    value: Mapped[str] = mapped_column(String(255), index=True, comment="Blacklisted word or IOC value, lowercased")
    type: Mapped[str] = mapped_column(String(10), comment="'word' or 'ioc'")
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), comment="When this entry was added"
    )

    @validates('value')
    def validate_value(self, key: str, value: str) -> str:
        if not value or not value.strip():
            raise ValueError("Blacklist value cannot be empty")
        return value.strip().lower()

    @validates('type')
    def validate_type(self, key: str, entry_type: str) -> str:
        if entry_type not in ("word", "ioc"):
            raise ValueError("Blacklist type must be 'word' or 'ioc'")
        return entry_type
