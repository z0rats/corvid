import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, JSON, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.core.database import Base


class MailSearch(Base):
    """A single mailcat email search run"""
    __tablename__ = "mail_searches"

    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(String(100), index=True)
    status: Mapped[str] = mapped_column(String(20), default="running", index=True)
    total_providers_checked: Mapped[int] = mapped_column(Integer, default=0)
    found_count: Mapped[int] = mapped_column(Integer, default=0)
    error_message: Mapped[str | None] = mapped_column(String(1000))
    started_at: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    completed_at: Mapped[datetime.datetime | None] = mapped_column(DateTime(timezone=True))

    provider_results: Mapped[list["MailSearchResult"]] = relationship(
        back_populates="search", passive_deletes=True, order_by="MailSearchResult.provider_name"
    )


class MailSearchResult(Base):
    """A single provider where the searched username/email was found registered.

    Only found providers are persisted here - checkers that returned no match
    are streamed live but not stored, matching username_search's MaigretSiteResult.
    """
    __tablename__ = "mail_search_results"

    id: Mapped[int] = mapped_column(primary_key=True)
    search_id: Mapped[int] = mapped_column(ForeignKey("mail_searches.id", ondelete="CASCADE"), index=True)
    provider_name: Mapped[str] = mapped_column(String(200))
    emails: Mapped[list[str]] = mapped_column(JSON)
    extra: Mapped[dict | None] = mapped_column(JSON)

    search: Mapped["MailSearch"] = relationship(back_populates="provider_results")
