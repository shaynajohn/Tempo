"""add strava connections

Revision ID: 002
Revises: 001
Create Date: 2026-06-07

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "002"
down_revision: Union[str, None] = "001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "strava_connections",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("athlete_id", sa.Integer(), nullable=False),
        sa.Column("athlete_name", sa.String(256), nullable=True),
        sa.Column("access_token", sa.String(512), nullable=False),
        sa.Column("refresh_token", sa.String(512), nullable=False),
        sa.Column("expires_at", sa.Integer(), nullable=False),
        sa.Column("scope", sa.String(512), nullable=True),
        sa.Column("last_synced_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_strava_connections_athlete_id",
        "strava_connections",
        ["athlete_id"],
        unique=True,
    )


def downgrade() -> None:
    op.drop_index("ix_strava_connections_athlete_id", table_name="strava_connections")
    op.drop_table("strava_connections")
