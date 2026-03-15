"""Add trust_pages table for public Trust Center feature.

Revision ID: 021
Revises: 020
Create Date: 2026-03-15 00:00:00.000000
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import UUID

revision = "021"
down_revision = "020"
branch_labels = None
depends_on = None

_DEFAULT_FRAMEWORKS = '["soc2","iso27001","hipaa","gdpr","pci_dss","ccpa","nist_csf"]'


def upgrade() -> None:
    op.create_table(
        "trust_pages",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "company_id",
            UUID(as_uuid=True),
            sa.ForeignKey("companies.id", ondelete="CASCADE"),
            unique=True,
            nullable=False,
        ),
        sa.Column("slug", sa.String(100), unique=True, nullable=False),
        sa.Column("is_enabled", sa.Boolean, nullable=False, server_default="true"),
        sa.Column("show_score", sa.Boolean, nullable=False, server_default="true"),
        sa.Column("show_policies", sa.Boolean, nullable=False, server_default="true"),
        sa.Column("show_integrations", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("custom_headline", sa.Text, nullable=True),
        sa.Column("custom_message", sa.Text, nullable=True),
        sa.Column("frameworks_json", sa.Text, nullable=False, server_default=f"'{_DEFAULT_FRAMEWORKS}'"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_trust_pages_slug", "trust_pages", ["slug"])
    op.create_index("ix_trust_pages_company_id", "trust_pages", ["company_id"])


def downgrade() -> None:
    op.drop_index("ix_trust_pages_slug", table_name="trust_pages")
    op.drop_index("ix_trust_pages_company_id", table_name="trust_pages")
    op.drop_table("trust_pages")
