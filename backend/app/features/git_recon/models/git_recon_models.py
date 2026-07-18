import datetime

from sqlalchemy import DateTime, Integer, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from app.core.database import Base


class GitReconSearch(Base):
    """A single git/GitHub identity-correlation search (gitcolombo)"""
    __tablename__ = "git_recon_searches"

    id: Mapped[int] = mapped_column(primary_key=True)
    mode: Mapped[str] = mapped_column(String(20))
    target: Mapped[str] = mapped_column(String(300), index=True)
    status: Mapped[str] = mapped_column(String(20), default="completed")
    error: Mapped[str | None] = mapped_column(Text)
    repos_scanned: Mapped[int] = mapped_column(Integer, default=0)
    repos_failed: Mapped[int] = mapped_column(Integer, default=0)
    persons_found: Mapped[int] = mapped_column(Integer, default=0)
    searched_at: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    result: Mapped[dict | None] = mapped_column(JSON)
