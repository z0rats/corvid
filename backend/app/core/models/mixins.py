import datetime

from sqlalchemy import DateTime, String
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func


class TimestampMixin:
    """`created_at`/`updated_at` columns, populated by the DB (`server_default`/`onupdate`).

    Reserved for CRUD row-creation/last-write timestamps. Domain-meaningful times
    (e.g. `started_at`/`completed_at` on scan models, `fetched_at` on articles) are
    intentionally distinct concepts and should keep their own names rather than
    being renamed to fit this mixin. See docs/database-schema-audit.md section 6,
    phase 3 (finding #5).
    """

    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), comment="When this row was created"
    )
    updated_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(),
        comment="When this row was last updated",
    )


class PypiVersionCheckMixin:
    """`latest_pypi_version`/`pypi_checked_at` columns for the manual "check for a newer
    version of this vendored OSINT tool" pattern (`email_search`/`username_search`'s two
    sources each poll PyPI on demand rather than at import time).

    Was three copies of the identical two columns across `EmailSearchConfig`,
    `SocialAnalyzerConfig`, `UsernameSearchConfig` before this existed. See
    docs/database-schema-audit.md section 6, phase 3 addendum.
    """

    latest_pypi_version: Mapped[str | None] = mapped_column(
        String(50), comment="Latest version seen on PyPI for the vendored tool, cached from the last manual check"
    )
    pypi_checked_at: Mapped[datetime.datetime | None] = mapped_column(
        DateTime(timezone=True), comment="When latest_pypi_version was last refreshed"
    )
