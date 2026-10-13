"""add parent_search_id, pivot_source and site_statuses to maigret_searches

Revision ID: c5e18a3d9f20
Revises: b3d90f1a7c55
Create Date: 2026-10-05 22:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "c5e18a3d9f20"
down_revision: str | None = "b3d90f1a7c55"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Plain ADD COLUMN, not batch_alter_table: on SQLite a batch recreates `maigret_searches`, and
    # with the app's `PRAGMA foreign_keys=ON` that cascades into every `maigret_site_results` row.
    # `parent_search_id` is not a foreign key for the same reason (SQLite cannot add one by ALTER).
    op.add_column(
        "maigret_searches",
        sa.Column(
            "parent_search_id",
            sa.Integer(),
            nullable=True,
            comment=(
                "MaigretSearch.id of the run whose pivot this run followed. Deliberately not a "
                "foreign key (SQLite cannot add one via ALTER): the parent may be deleted later, "
                "leaving a dangling id readers must tolerate"
            ),
        ),
    )
    op.add_column(
        "maigret_searches",
        sa.Column(
            "pivot_source",
            sa.String(length=200),
            nullable=True,
            comment="Client-supplied label for the pivot this run followed (untrusted text)",
        ),
    )
    op.add_column(
        "maigret_searches",
        sa.Column(
            "site_statuses",
            sa.JSON(),
            nullable=True,
            comment=(
                "Site checks only (a Maigret run on named sites): site name -> Maigret verdict "
                "(claimed, available, unknown, illegal), so a blocked check isn't read as not "
                "found. NULL for a full scan"
            ),
        ),
    )
    op.create_index(
        op.f("ix_maigret_searches_parent_search_id"),
        "maigret_searches",
        ["parent_search_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_maigret_searches_parent_search_id"), table_name="maigret_searches")
    op.drop_column("maigret_searches", "site_statuses")
    op.drop_column("maigret_searches", "pivot_source")
    op.drop_column("maigret_searches", "parent_search_id")
