import datetime

from sqlalchemy import JSON, CheckConstraint, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.core.database import Base


class PhoneSearch(Base):
    """A single phone-number registration search run"""

    __tablename__ = "phone_searches"
    __table_args__ = (
        CheckConstraint(
            "status IN ('running', 'completed', 'cancelled', 'failed')",
            name="ck_phone_searches_status",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True, comment="Surrogate primary key")
    phone_number: Mapped[str] = mapped_column(
        String(20), index=True, comment="E.164 phone number searched across providers"
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
        Integer, default=0, comment="Providers where the number was found registered"
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

    provider_results: Mapped[list[PhoneSearchResult]] = relationship(
        back_populates="search", passive_deletes=True, order_by="PhoneSearchResult.provider_name"
    )


class PhoneSearchResult(Base):
    """A single provider where the searched phone number was found registered.

    Only found providers are persisted here - checkers that returned no match
    are streamed live but not stored, matching email_search's MailSearchResult.
    """

    __tablename__ = "phone_search_results"

    id: Mapped[int] = mapped_column(primary_key=True, comment="Surrogate primary key")
    search_id: Mapped[int] = mapped_column(
        ForeignKey("phone_searches.id", ondelete="CASCADE"),
        index=True,
        comment="Owning PhoneSearch.id",
    )
    provider_name: Mapped[str] = mapped_column(
        String(100), comment="Provider/service where the number was found registered"
    )
    extra: Mapped[dict | None] = mapped_column(
        JSON, comment="Provider-specific extras not worth their own columns"
    )

    search: Mapped[PhoneSearch] = relationship(back_populates="provider_results")
