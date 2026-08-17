"""fix null literal json values in news_articles

The NewsArticle.matches/iocs/relevant_iocs columns used the plain sqlalchemy
JSON type, whose default none_as_null=False persists a Python None as the
4-character text "null" rather than a real SQL NULL. That defeated
apply_article_filters' `column.is_not(None)` check (a stored "null" string
is never SQL NULL), so the newsfeed UI's "has IOCs"/"has matches" filters
silently returned every article regardless of whether it actually had any.
The model now sets none_as_null=True so newly written rows get real NULLs;
this backfills existing rows written under the old default.

Revision ID: bf5e06e441df
Revises: e541fd2b2817
Create Date: 2026-08-04 22:48:20.414242

"""

from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "bf5e06e441df"
down_revision: str | None = "e541fd2b2817"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_JSON_NULL_COLUMNS = ("matches", "iocs", "relevant_iocs")


def upgrade() -> None:
    for column in _JSON_NULL_COLUMNS:
        op.execute(f"UPDATE news_articles SET {column} = NULL WHERE {column} = 'null'")


def downgrade() -> None:
    # One-way data fix: turning a real SQL NULL back into the literal text
    # "null" would just reintroduce the bug, so there's nothing to reverse.
    pass
