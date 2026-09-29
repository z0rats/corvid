import datetime

from sqlalchemy import JSON, Boolean, DateTime, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from app.core.database import Base


class AmassSearch(Base):
    """A single amass active-enumeration scan for a domain"""

    __tablename__ = "amass_searches"

    id: Mapped[int] = mapped_column(primary_key=True, comment="Surrogate primary key")
    domain: Mapped[str] = mapped_column(String(255), index=True, comment="Domain that was scanned")
    brute_force: Mapped[bool] = mapped_column(
        Boolean, default=False, comment="Whether wordlist brute-forcing was enabled for this scan"
    )
    status: Mapped[str] = mapped_column(
        String(20), default="completed", comment="running, completed, cancelled, or failed"
    )
    error: Mapped[str | None] = mapped_column(Text, comment="Error detail if status is failed")
    hosts_found: Mapped[int] = mapped_column(
        Integer, default=0, comment="Distinct hosts found for this domain at scan completion"
    )
    searched_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), comment="When the search ran"
    )
    result: Mapped[dict | None] = mapped_column(
        JSON,
        comment=(
            "Full {'hosts': [{'hostname', 'ip'}, ...]} result - amass's engine accumulates "
            "findings for a domain across every scan ever run against it (see "
            "docs/architecture/amass.md), so this reflects everything currently known at "
            "the time this scan completed, not only what changed during this specific run"
        ),
    )
