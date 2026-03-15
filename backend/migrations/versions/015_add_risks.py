"""Add risks table for risk register.

Revision ID: 015
Revises: 014
Create Date: 2026-03-15 00:00:00.000000
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import UUID

revision = "015"
down_revision = "014"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "risks",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "company_id",
            UUID(as_uuid=True),
            sa.ForeignKey("companies.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("category", sa.String(100), nullable=False, server_default="General"),
        sa.Column("likelihood", sa.Integer, nullable=False, server_default="3"),
        sa.Column("impact", sa.Integer, nullable=False, server_default="3"),
        sa.Column("status", sa.String(50), nullable=False, server_default="open"),
        sa.Column(
            "owner_user_id",
            UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("notes", sa.Text, nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )
    op.create_index("ix_risks_company_id", "risks", ["company_id"])
    op.create_index("ix_risks_company_status", "risks", ["company_id", "status"])


def downgrade() -> None:
    op.drop_index("ix_risks_company_status", table_name="risks")
    op.drop_index("ix_risks_company_id", table_name="risks")
    op.drop_table("risks")
