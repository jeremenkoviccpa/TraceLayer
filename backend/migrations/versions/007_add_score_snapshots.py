"""Add compliance score snapshots table.

Revision ID: 007
Revises: 006
Create Date: 2026-03-14
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

revision = "007"
down_revision = "006"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "compliance_score_snapshots",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("company_id", UUID(as_uuid=True), sa.ForeignKey("companies.id", ondelete="CASCADE"), nullable=False),
        sa.Column("framework", sa.String(50), nullable=False),
        sa.Column("overall_score", sa.Integer, nullable=False),
        sa.Column("snapshot_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index(
        "ix_score_snapshots_company_fw_at",
        "compliance_score_snapshots",
        ["company_id", "framework", "snapshot_at"],
    )


def downgrade() -> None:
    op.drop_index("ix_score_snapshots_company_fw_at", table_name="compliance_score_snapshots")
    op.drop_table("compliance_score_snapshots")
