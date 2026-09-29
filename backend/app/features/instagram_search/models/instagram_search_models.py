import datetime
from typing import Any

from sqlalchemy import JSON, Boolean, CheckConstraint, DateTime, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from app.core.database import Base


class InstagramSearch(Base):
    """A single followers/followees/posts scan of an Instagram profile (Phase 2 -
    the profile-metadata lookup itself, Phase 1, stays ephemeral, no history)."""

    __tablename__ = "instagram_searches"
    __table_args__ = (
        CheckConstraint(
            "status IN ('running', 'completed', 'cancelled', 'failed')",
            name="ck_instagram_searches_status",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True, comment="Surrogate primary key")
    scan_type: Mapped[str] = mapped_column(
        String(20), comment="'followers', 'followees', or 'posts'"
    )
    username: Mapped[str] = mapped_column(
        String(60), index=True, comment="Instagram username that was scanned"
    )
    mode: Mapped[str] = mapped_column(
        String(20), comment="'anonymous' or 'session' - which one the scan actually ran as"
    )
    status: Mapped[str] = mapped_column(
        String(20), default="completed", comment="running, completed, cancelled, or failed"
    )
    error: Mapped[str | None] = mapped_column(Text, comment="Error detail if status is failed")
    item_count: Mapped[int] = mapped_column(
        Integer, default=0, comment="Items actually collected before stopping"
    )
    total_count: Mapped[int | None] = mapped_column(
        Integer, comment="Instagram-reported total count, when the API exposed one"
    )
    truncated: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        comment="Hit the per-scan item cap or wall-clock deadline before exhausting the list",
    )
    searched_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), comment="When the scan ran"
    )
    result: Mapped[list[dict[str, Any]] | None] = mapped_column(
        JSON,
        comment=(
            "Full items list blob (shape depends on scan_type) - no normalized child "
            "table, same pattern as GitReconSearch.result"
        ),
    )

    @property
    def items(self) -> list[dict[str, Any]]:
        """Alias read by `InstagramScanDetail.model_validate(..., from_attributes=True)` -
        the schema calls it `items` (what it actually is); the column stays `result` for
        parity with GitReconSearch's naming."""
        return self.result or []
