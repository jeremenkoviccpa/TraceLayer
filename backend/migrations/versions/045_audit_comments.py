"""Add audit_comments table

Revision ID: 045_audit_comments
Revises: 044_employee_portal_slack
Create Date: 2026-03-23
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "045_audit_comments"
down_revision = "044_employee_portal_slack"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "audit_comments",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "engagement_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("audit_engagements.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "company_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("companies.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("author_name", sa.String(255), nullable=False),
        sa.Column("author_role", sa.String(20), nullable=False),
        sa.Column(
            "author_user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("body", sa.Text, nullable=False),
        sa.Column("item_type", sa.String(50), nullable=True),
        sa.Column("item_ref", sa.String(255), nullable=True),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), server_default=sa.text("now()")),
    )
    op.create_index("ix_audit_comments_engagement", "audit_comments", ["engagement_id"])


def downgrade() -> None:
    op.drop_index("ix_audit_comments_engagement", table_name="audit_comments")
    op.drop_table("audit_comments")
