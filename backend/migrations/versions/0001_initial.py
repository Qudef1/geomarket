"""Initial PostGIS-backed analysis tables."""

from collections.abc import Sequence

import geoalchemy2
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "0001"
down_revision = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS postgis")
    op.create_table(
        "analyses",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("business_type", sa.String(50), nullable=False),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("request", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_table(
        "candidates",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "analysis_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("analyses.id", ondelete="CASCADE"),
        ),
        sa.Column(
            "location",
            geoalchemy2.Geography("POINT", srid=4326, spatial_index=False),
            nullable=False,
        ),
        sa.Column("score", sa.Float(), nullable=False),
        sa.Column("features", sa.JSON(), nullable=False),
        sa.Column("explanation", sa.JSON(), nullable=False),
    )
    op.create_index("ix_candidates_location", "candidates", ["location"], postgresql_using="gist")


def downgrade() -> None:
    op.drop_index("ix_candidates_location", table_name="candidates")
    op.drop_table("candidates")
    op.drop_table("analyses")
