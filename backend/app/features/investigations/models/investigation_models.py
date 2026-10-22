import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.core.database import Base
from app.core.models.mixins import TimestampMixin


class Investigation(Base, TimestampMixin):
    """A named collection of references to runs of other features, see
    docs/adr/0027-investigations-reference-runs.md"""

    __tablename__ = "investigations"

    id: Mapped[int] = mapped_column(primary_key=True, comment="Surrogate primary key")
    name: Mapped[str] = mapped_column(String(200), comment="Analyst-given name")
    notes: Mapped[str | None] = mapped_column(Text, comment="Free-text analyst notes")

    items: Mapped[list[InvestigationItem]] = relationship(
        back_populates="investigation",
        cascade="all, delete-orphan",
        passive_deletes=True,
        order_by="InvestigationItem.added_at",
    )


class InvestigationItem(Base, TimestampMixin):
    """One run of one feature, referenced by (feature, run_id) - not copied"""

    __tablename__ = "investigation_items"
    __table_args__ = (
        UniqueConstraint(
            "investigation_id", "feature", "run_id", name="uq_investigation_item_feature_run"
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True, comment="Surrogate primary key")
    investigation_id: Mapped[int] = mapped_column(
        ForeignKey("investigations.id", ondelete="CASCADE"),
        index=True,
        comment="Owning Investigation.id",
    )
    feature: Mapped[str] = mapped_column(
        String(50), comment="Activity-feed feature name, e.g. 'ioc_lookup', 'username_search'"
    )
    run_id: Mapped[int] = mapped_column(
        Integer,
        comment=(
            "Id of the run in that feature's own table. Deliberately not a foreign key (it "
            "points into a different table per feature): the run may be deleted from history, "
            "leaving a tombstone readers must tolerate"
        ),
    )
    target: Mapped[str] = mapped_column(
        String(2000),
        comment="What the run was about (username, IOC, ...) when added, kept for tombstones",
    )
    note: Mapped[str | None] = mapped_column(Text, comment="Analyst note on this item")
    added_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        comment="When the run was added to the investigation",
    )

    investigation: Mapped[Investigation] = relationship(back_populates="items")
