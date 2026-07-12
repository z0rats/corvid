import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, JSON, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.core.database import Base


class RedditSearch(Base):
    """A single Reddit user-history search (Arctic Shift + PullPush archives)"""
    __tablename__ = "reddit_searches"

    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(String(100), index=True)
    subreddit_filter: Mapped[str | None] = mapped_column(String(100))
    date_from: Mapped[int | None] = mapped_column(Integer)
    date_to: Mapped[int | None] = mapped_column(Integer)
    include_nsfw: Mapped[bool] = mapped_column(Boolean, default=True)
    searched_at: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    results: Mapped[list["RedditSearchResult"]] = relationship(
        back_populates="search", passive_deletes=True, order_by="RedditSearchResult.created_utc.desc()"
    )


class RedditSearchResult(Base):
    """A single post or comment found for the searched username, from either archive"""
    __tablename__ = "reddit_search_results"
    __table_args__ = (
        UniqueConstraint("search_id", "kind", "reddit_id", name="uq_reddit_result_search_kind_id"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    search_id: Mapped[int] = mapped_column(ForeignKey("reddit_searches.id", ondelete="CASCADE"), index=True)
    kind: Mapped[str] = mapped_column(String(10))
    reddit_id: Mapped[str] = mapped_column(String(20))
    subreddit: Mapped[str] = mapped_column(String(100))
    title: Mapped[str | None] = mapped_column(Text)
    body: Mapped[str | None] = mapped_column(Text)
    score: Mapped[int] = mapped_column(Integer, default=0)
    num_comments: Mapped[int | None] = mapped_column(Integer)
    permalink: Mapped[str] = mapped_column(String(500))
    created_utc: Mapped[int] = mapped_column(Integer, index=True)
    over_18: Mapped[bool] = mapped_column(Boolean, default=False)
    removed: Mapped[bool] = mapped_column(Boolean, default=False)
    deleted: Mapped[bool] = mapped_column(Boolean, default=False)
    extra: Mapped[dict | None] = mapped_column(JSON)

    search: Mapped["RedditSearch"] = relationship(back_populates="results")
