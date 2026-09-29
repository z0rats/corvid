import datetime

from sqlalchemy import JSON, CheckConstraint, DateTime, Float, Integer, String
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from app.core.database import Base


class SteamReconSearch(Base):
    """A single Steam Recon scan: friends-graph collection, close-friends ranking,
    geolocation-by-social-graph, and (optionally) the CS2 cheater-probability report.

    No child-row tables - the friends graph, close-friends list, geolocation hypothesis
    and cheater report are all persisted as one `result` JSON blob (same shape git_recon's
    `GitReconSearch.result` uses, see database-schema-audit.md #12), since none of them
    are ever queried independently of the scan they came from.
    """

    __tablename__ = "steam_recon_searches"
    __table_args__ = (
        CheckConstraint(
            "status IN ('running', 'completed', 'cancelled', 'failed')",
            name="ck_steam_recon_searches_status",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True, comment="Surrogate primary key")
    target: Mapped[str] = mapped_column(
        String(512), comment="Raw target input (SteamID/URL/vanity) as the user entered it"
    )
    steamid64: Mapped[str | None] = mapped_column(
        String(20), index=True, comment="Resolved target SteamID64, once resolution succeeds"
    )
    persona_name: Mapped[str | None] = mapped_column(
        String(200), comment="Target's persona name at scan time"
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
    max_friends: Mapped[int] = mapped_column(Integer, comment="Friend cap requested for this scan")
    include_cs_report: Mapped[bool] = mapped_column(
        comment="Whether the CS2 cheater-probability report was requested"
    )
    friends_total: Mapped[int] = mapped_column(
        Integer, default=0, comment="Total friends on the target's friend list"
    )
    friends_analyzed: Mapped[int] = mapped_column(
        Integer, default=0, comment="Friends whose own friend list was successfully fetched"
    )
    friends_located: Mapped[int] = mapped_column(
        Integer, default=0, comment="Analyzed friends with a usable location"
    )
    top_country_code: Mapped[str | None] = mapped_column(
        String(8), comment="Leading country hypothesis's ISO code, for the history list"
    )
    cheater_probability: Mapped[float | None] = mapped_column(
        Float, comment="CS2 cheater-probability estimate (0-1), when include_cs_report was set"
    )
    started_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), comment="When the scan started"
    )
    completed_at: Mapped[datetime.datetime | None] = mapped_column(
        DateTime(timezone=True), comment="When the scan finished, if it has"
    )
    result: Mapped[dict | None] = mapped_column(
        JSON, comment="Full scan result blob: profile, close_friends, geolocation, cheater_report"
    )
