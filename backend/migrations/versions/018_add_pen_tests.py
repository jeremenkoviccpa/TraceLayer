"""Add pen_tests table for penetration test tracker.

Revision ID: 018
Revises: 017
Create Date: 2026-03-15 00:00:00.000000
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import UUID

revision = "018"
down_revision = "017"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "pen_tests",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "company_id",
            UUID(as_uuid=True),
            sa.ForeignKey("companies.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("vendor_name", sa.String(255), nullable=False),
        sa.Column("status", sa.String(50), nullable=False, server_default="scheduled"),
        sa.Column("scope", sa.Text, nullable=True),
        sa.Column("conducted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("next_scheduled_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("critical_count", sa.Integer, nullable=False, server_default="0"),
        sa.Column("high_count", sa.Integer, nullable=False, server_default="0"),
        sa.Column("medium_count", sa.Integer, nullable=False, server_default="0"),
        sa.Column("low_count", sa.Integer, nullable=False, server_default="0"),
        sa.Column("summary", sa.Text, nullable=True),
        sa.Column("file_url", sa.String(1024), nullable=True),
        sa.Column("remediation_notes", sa.Text, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_pen_tests_company_id", "pen_tests", ["company_id"])


def downgrade() -> None:
    op.drop_index("ix_pen_tests_company_id", table_name="pen_tests")
    op.drop_table("pen_tests")
