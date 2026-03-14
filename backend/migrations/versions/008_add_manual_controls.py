"""Add manual_controls table for non-automated compliance checks.

Revision ID: 008
Revises: 007
Create Date: 2026-03-14
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import UUID

revision = "008"
down_revision = "007"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "manual_controls",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "company_id",
            UUID(as_uuid=True),
            sa.ForeignKey("companies.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("framework", sa.String(50), nullable=False),
        sa.Column("control_id", sa.String(100), nullable=False),
        sa.Column("status", sa.String(50), nullable=False, server_default="pending"),
        sa.Column("notes", sa.Text, nullable=True),
        sa.Column(
            "updated_by_id",
            UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.UniqueConstraint("company_id", "framework", "control_id", name="uq_manual_control"),
    )
    op.create_index(
        "ix_manual_controls_company_framework",
        "manual_controls",
        ["company_id", "framework"],
    )


def downgrade() -> None:
    op.drop_index("ix_manual_controls_company_framework", table_name="manual_controls")
    op.drop_table("manual_controls")
