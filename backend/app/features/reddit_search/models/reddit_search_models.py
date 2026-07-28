import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, JSON, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.core.database import Base


class RedditSearch(Base):
    """A single Reddit user-history search (Arctic Shift + PullPush archives)"""
    __tablename__ = "reddit_searches"

    id: Mapped[int] = mapped_column(primary_key=True, comment="Surrogate primary key")
    username: Mapped[str] = mapped_column(String(100), index=True, comment="Reddit username searched")
    subreddit_filter: Mapped[str | None] = mapped_column(String(100), comment="Optional single subreddit to restrict to")
    date_from: Mapped[int | None] = mapped_column(
        Integer, comment="unix timestamp, not DateTime - Arctic Shift/PullPush take unix cursors"
    )
    date_to: Mapped[int | None] = mapped_column(
        Integer, comment="unix timestamp, not DateTime - Arctic Shift/PullPush take unix cursors"
    )
    include_nsfw: Mapped[bool] = mapped_column(Boolean, default=True, comment="Whether NSFW-flagged content is included")
    searched_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), comment="When the search ran"
    )

    results: Mapped[list["RedditSearchResult"]] = relationship(
        back_populates="search", passive_deletes=True, order_by="RedditSearchResult.created_utc.desc()"
    )


class RedditSearchResult(Base):
    """A single post or comment found for the searched username, from either archive"""
    __tablename__ = "reddit_search_results"
    __table_args__ = (
        UniqueConstraint("search_id", "kind", "reddit_id", name="uq_reddit_result_search_kind_id"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, comment="Surrogate primary key")
    search_id: Mapped[int] = mapped_column(
        ForeignKey("reddit_searches.id", ondelete="CASCADE"), index=True, comment="Owning RedditSearch.id"
    )
    kind: Mapped[str] = mapped_column(String(10), comment="'post' or 'comment'")
    reddit_id: Mapped[str] = mapped_column(String(20), comment="Reddit's own id for this post/comment (stable across runs)")
    subreddit: Mapped[str] = mapped_column(String(100), comment="Subreddit the post/comment was made in")
    title: Mapped[str | None] = mapped_column(Text, comment="Post title (null for comments)")
    body: Mapped[str | None] = mapped_column(Text, comment="Post selftext or comment body")
    score: Mapped[int] = mapped_column(Integer, default=0, comment="Reddit score/upvotes at time of fetch")
    num_comments: Mapped[int | None] = mapped_column(Integer, comment="Comment count at time of fetch (posts only)")
    permalink: Mapped[str] = mapped_column(String(500), comment="Relative Reddit URL to the post/comment")
    created_utc: Mapped[int] = mapped_column(
        Integer, index=True, comment="unix timestamp, not DateTime - as returned by Arctic Shift/PullPush"
    )
    over_18: Mapped[bool] = mapped_column(Boolean, default=False, comment="Whether the post/comment is NSFW-flagged")
    removed: Mapped[bool] = mapped_column(Boolean, default=False, comment="Whether the post/comment was removed by mods")
    deleted: Mapped[bool] = mapped_column(Boolean, default=False, comment="Whether the author deleted the post/comment")
    extra: Mapped[dict | None] = mapped_column(JSON, comment="Source-specific extras not worth their own columns")

    search: Mapped["RedditSearch"] = relationship(back_populates="results")
