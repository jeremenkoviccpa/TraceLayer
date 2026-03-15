"""Add access_reviews table for quarterly access review workflows.

Revision ID: 020
Revises: 019
Create Date: 2026-03-15 00:00:00.000000
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import UUID

revision = "020"
down_revision = "019"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "access_reviews",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "company_id",
            UUID(as_uuid=True),
            sa.ForeignKey("companies.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("period", sa.String(50), nullable=False),
        sa.Column(
            "reviewer_user_id",
            UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("status", sa.String(50), nullable=False, server_default="open"),
        sa.Column("due_date", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("users_reviewed", sa.Integer, nullable=False, server_default="0"),
        sa.Column("access_changes", sa.Integer, nullable=False, server_default="0"),
        sa.Column("scope", sa.Text, nullable=True),
        sa.Column("findings", sa.Text, nullable=True),
        sa.Column("notes", sa.Text, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_access_reviews_company_id", "access_reviews", ["company_id"])


def downgrade() -> None:
    op.drop_index("ix_access_reviews_company_id", table_name="access_reviews")
    op.drop_table("access_reviews")
