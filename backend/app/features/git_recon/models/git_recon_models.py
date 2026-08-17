import datetime

from sqlalchemy import JSON, DateTime, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from app.core.database import Base


class GitReconSearch(Base):
    """A single git/GitHub identity-correlation search (gitcolombo)"""

    __tablename__ = "git_recon_searches"

    id: Mapped[int] = mapped_column(primary_key=True, comment="Surrogate primary key")
    mode: Mapped[str] = mapped_column(
        String(20), comment="gitcolombo scan mode (e.g. 'user', 'org', 'repo')"
    )
    target: Mapped[str] = mapped_column(
        String(300), index=True, comment="GitHub user/org/repo that was scanned"
    )
    status: Mapped[str] = mapped_column(
        String(20), default="completed", comment="running, completed, cancelled, or failed"
    )
    error: Mapped[str | None] = mapped_column(Text, comment="Error detail if status is failed")
    repos_scanned: Mapped[int] = mapped_column(
        Integer, default=0, comment="Repositories successfully scanned"
    )
    repos_failed: Mapped[int] = mapped_column(
        Integer, default=0, comment="Repositories that failed to scan"
    )
    persons_found: Mapped[int] = mapped_column(
        Integer, default=0, comment="Distinct identities correlated"
    )
    searched_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), comment="When the search ran"
    )
    result: Mapped[dict | None] = mapped_column(
        JSON,
        comment=(
            "Full gitcolombo result blob - no normalized result table, see "
            "database-schema-audit.md #12"
        ),
    )
