import datetime
import uuid

from sqlalchemy import DateTime, ForeignKey, JSON, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship, validates
from sqlalchemy.sql import func

from app.core.database import Base


def generate_icon_id() -> str:
    return str(uuid.uuid4())


class NewsfeedSettings(Base):
    __tablename__ = "newsfeed_settings"

    name: Mapped[str] = mapped_column(String, primary_key=True)
    url: Mapped[str] = mapped_column(String)
    icon: Mapped[str] = mapped_column(String, default='default.png')
    icon_id: Mapped[str] = mapped_column(String, default=generate_icon_id)
    enabled: Mapped[bool] = mapped_column(default=True)
    deleted: Mapped[bool] = mapped_column(default=False)

    articles: Mapped[list["NewsArticle"]] = relationship(back_populates="feed", passive_deletes=True)


class NewsArticle(Base):
    __tablename__ = 'news_articles'

    id: Mapped[int] = mapped_column(primary_key=True)
    feedname: Mapped[str] = mapped_column(String, ForeignKey("newsfeed_settings.name", ondelete="CASCADE"), index=True)
    icon: Mapped[str] = mapped_column(String)
    title: Mapped[str] = mapped_column(String)
    summary: Mapped[str] = mapped_column(String)
    full_text: Mapped[str | None] = mapped_column(String)
    date: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True), index=True)
    link: Mapped[str] = mapped_column(String, unique=True, index=True)
    fetched_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.datetime.now(datetime.timezone.utc)
    )
    matches: Mapped[list[str] | None] = mapped_column(JSON)
    iocs: Mapped[dict[str, list[str]] | None] = mapped_column(JSON)
    relevant_iocs: Mapped[list[str] | None] = mapped_column(JSON)
    analysis_result: Mapped[str | None] = mapped_column(Text)
    note: Mapped[str | None] = mapped_column(Text)
    tlp: Mapped[str] = mapped_column(String, default="TLP:CLEAR")
    read: Mapped[bool] = mapped_column(default=False)

    feed: Mapped["NewsfeedSettings"] = relationship(back_populates="articles")


class NewsfeedConfig(Base):
    __tablename__ = 'newsfeed_config'

    id: Mapped[int] = mapped_column(primary_key=True)
    retention_days: Mapped[int] = mapped_column(default=0)
    background_fetch_enabled: Mapped[bool] = mapped_column(default=True)
    fetch_interval_minutes: Mapped[int] = mapped_column(default=60)
    last_fetch_timestamp: Mapped[datetime.datetime | None] = mapped_column(DateTime(timezone=True))
    keyword_matching_enabled: Mapped[bool] = mapped_column(default=False)


class TrendsBlacklistEntry(Base):
    """Blacklisted words and IOC values excluded from trends analytics"""
    __tablename__ = 'trends_blacklist'
    __table_args__ = (UniqueConstraint('value', 'type', name='uq_blacklist_value_type'),)

    id: Mapped[int] = mapped_column(primary_key=True)
    value: Mapped[str] = mapped_column(String(255), index=True)
    type: Mapped[str] = mapped_column(String(10))
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

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
