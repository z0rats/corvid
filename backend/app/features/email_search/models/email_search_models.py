import datetime

from sqlalchemy import JSON, CheckConstraint, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.core.database import Base


class MailSearch(Base):
    """A single mailcat email search run"""

    __tablename__ = "mail_searches"
    __table_args__ = (
        CheckConstraint(
            "status IN ('running', 'completed', 'cancelled', 'failed')",
            name="ck_mail_searches_status",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True, comment="Surrogate primary key")
    username: Mapped[str] = mapped_column(
        String(100), index=True, comment="Username/email searched across providers"
    )
    status: Mapped[str] = mapped_column(
        String(20),
        default="running",
        index=True,
        comment="running, completed, cancelled, or failed",
    )
    total_providers_checked: Mapped[int] = mapped_column(
        Integer, default=0, comment="Providers checked so far"
    )
    found_count: Mapped[int] = mapped_column(
        Integer, default=0, comment="Providers where a registered account was found"
    )
    error_message: Mapped[str | None] = mapped_column(
        String(1000), comment="Error detail if status is failed"
    )
    started_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), comment="When the search run started"
    )
    completed_at: Mapped[datetime.datetime | None] = mapped_column(
        DateTime(timezone=True), comment="When the search run finished, if it has"
    )

    provider_results: Mapped[list[MailSearchResult]] = relationship(
        back_populates="search", passive_deletes=True, order_by="MailSearchResult.provider_name"
    )


class MailSearchResult(Base):
    """A single provider where the searched username/email was found registered.

    Only found providers are persisted here - checkers that returned no match
    are streamed live but not stored, matching username_search's MaigretSiteResult.
    """

    __tablename__ = "mail_search_results"

    id: Mapped[int] = mapped_column(primary_key=True, comment="Surrogate primary key")
    search_id: Mapped[int] = mapped_column(
        ForeignKey("mail_searches.id", ondelete="CASCADE"),
        index=True,
        comment="Owning MailSearch.id",
    )
    provider_name: Mapped[str] = mapped_column(
        String(200), comment="Provider/service where the account was found"
    )
    emails: Mapped[list[str]] = mapped_column(
        JSON, comment="Email address(es) found registered with this provider"
    )
    extra: Mapped[dict | None] = mapped_column(
        JSON, comment="Provider-specific extras not worth their own columns"
    )

    search: Mapped[MailSearch] = relationship(back_populates="provider_results")
