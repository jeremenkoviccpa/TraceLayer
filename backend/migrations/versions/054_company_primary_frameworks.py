"""Add primary_frameworks JSONB column to companies table.

Stores the ordered list of compliance frameworks the company selected during
onboarding (or later in settings). The dashboard uses this to pin and reorder
frameworks so the ones the company cares about appear first.

Revision ID: 054_company_primary_frameworks
Revises: 053_dpdp_certin_fw_versions
Create Date: 2026-03-29
"""
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "054_company_primary_frameworks"
down_revision = "053_dpdp_certin_fw_versions"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "companies",
        sa.Column(
            "primary_frameworks",
            postgresql.JSONB(),
            server_default=sa.text("'[]'::jsonb"),
            nullable=False,
        ),
    )


def downgrade() -> None:
    op.drop_column("companies", "primary_frameworks")
