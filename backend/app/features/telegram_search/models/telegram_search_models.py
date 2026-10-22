import datetime

from sqlalchemy import JSON, CheckConstraint, DateTime, Integer, String
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from app.core.database import Base


class TelegramChannelSearch(Base):
    """One analytics run over a public Telegram channel or group: profile card, sampled posts,
    activity metrics and extracted indicators. Everything past the summary columns lives in one
    `result` JSON blob (docs/adr/0002-git-recon-json-blob-results.md), since none of it is
    queried on its own."""

    __tablename__ = "telegram_channel_searches"
    __table_args__ = (
        CheckConstraint(
            "status IN ('running', 'completed', 'cancelled', 'failed')",
            name="ck_telegram_channel_searches_status",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True, comment="Surrogate primary key")
    target: Mapped[str] = mapped_column(
        String(200), comment="Raw input (@name, name or t.me link) as the user entered it"
    )
    channel: Mapped[str] = mapped_column(
        String(32), index=True, comment="Normalized lowercase channel username"
    )
    title: Mapped[str | None] = mapped_column(String(255), comment="Channel title at scan time")
    kind: Mapped[str | None] = mapped_column(
        String(16), comment="channel, group or unknown, from the t.me card"
    )
    member_count: Mapped[int | None] = mapped_column(
        Integer, comment="Subscribers (channel) or members (group) at scan time"
    )
    status: Mapped[str] = mapped_column(
        String(20),
        default="running",
        index=True,
        comment="running, completed, cancelled, or failed",
    )
    error_message: Mapped[str | None] = mapped_column(
        String(1000), comment="Error detail if status is failed"
    )
    max_posts: Mapped[int] = mapped_column(Integer, comment="Post sample size requested")
    posts_sampled: Mapped[int] = mapped_column(
        Integer, default=0, comment="Posts actually read from the web preview"
    )
    started_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), comment="When the scan started"
    )
    completed_at: Mapped[datetime.datetime | None] = mapped_column(
        DateTime(timezone=True), comment="When the scan finished, if it has"
    )
    result: Mapped[dict | None] = mapped_column(
        JSON, comment="Full result blob: profile, metrics, top_posts, posts, indicators"
    )
