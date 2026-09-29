"""add image geolocation searches table

Revision ID: ca2b89247773
Revises: 6a6114c9a268
Create Date: 2026-09-10 18:15:36.053500

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "ca2b89247773"
down_revision: str | None = "6a6114c9a268"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "image_geolocation_searches",
        sa.Column("id", sa.Integer(), nullable=False, comment="Surrogate primary key"),
        sa.Column(
            "filename",
            sa.String(length=500),
            nullable=False,
            comment="Original uploaded filename",
        ),
        sa.Column(
            "image_sha256",
            sa.String(length=64),
            nullable=False,
            comment="SHA256 of the analyzed image content",
        ),
        sa.Column(
            "model_used",
            sa.String(length=200),
            nullable=False,
            comment="ID of the LLM model that produced this analysis",
        ),
        sa.Column(
            "top_candidate",
            sa.String(length=500),
            nullable=True,
            comment="Location of the top-ranked candidate, if any",
        ),
        sa.Column(
            "top_confidence",
            sa.Float(),
            nullable=True,
            comment="Confidence of the top-ranked candidate, if any",
        ),
        sa.Column(
            "result",
            sa.JSON(),
            nullable=False,
            comment="Full candidates/clues/caveats payload (ImageGeolocationAIResult)",
        ),
        sa.Column(
            "searched_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("(CURRENT_TIMESTAMP)"),
            nullable=False,
            comment="When the analysis ran",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_image_geolocation_searches_image_sha256"),
        "image_geolocation_searches",
        ["image_sha256"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        op.f("ix_image_geolocation_searches_image_sha256"),
        table_name="image_geolocation_searches",
    )
    op.drop_table("image_geolocation_searches")
