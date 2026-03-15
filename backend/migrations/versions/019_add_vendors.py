"""Add vendors table for vendor due diligence tracking.

Revision ID: 019
Revises: 018
Create Date: 2026-03-15 00:00:00.000000
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import UUID

revision = "019"
down_revision = "018"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "vendors",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "company_id",
            UUID(as_uuid=True),
            sa.ForeignKey("companies.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("category", sa.String(100), nullable=False, server_default="other"),
        sa.Column("risk_level", sa.String(50), nullable=False, server_default="medium"),
        sa.Column("website", sa.String(512), nullable=True),
        sa.Column("contact_email", sa.String(255), nullable=True),
        sa.Column("soc2_certified", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("iso27001_certified", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("hipaa_certified", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("review_date", sa.DateTime(timezone=True), nullable=True),
        sa.Column("notes", sa.Text, nullable=True),
        sa.Column("report_file_url", sa.String(1024), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_vendors_company_id", "vendors", ["company_id"])


def downgrade() -> None:
    op.drop_index("ix_vendors_company_id", table_name="vendors")
    op.drop_table("vendors")
