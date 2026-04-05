"""Add tool_leads table for free tool email captures.

Revision ID: 059_add_tool_leads
Revises: 058_certin_incident_fields
Create Date: 2026-04-05
"""
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import UUID

revision = "059_add_tool_leads"
down_revision = "058_certin_incident_fields"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "tool_leads",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("email", sa.String(255), nullable=False),
        sa.Column("tool", sa.String(100), nullable=False),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_tool_leads_email", "tool_leads", ["email"])
    op.create_index("ix_tool_leads_created_at", "tool_leads", ["created_at"])


def downgrade() -> None:
    op.drop_table("tool_leads")
