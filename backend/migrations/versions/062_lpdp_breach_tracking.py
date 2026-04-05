"""Add LPDP Poverenik breach notification tracking fields to data_breaches.

Adds poverenik_notified_at and poverenik_ref_number so companies can track
their 72-hour breach notification obligation to the Serbian Commissioner
(Poverenik za informacije od javnog značaja i zaštitu podataka o ličnosti)
per Art. 53 of the Serbian LPDP.

Revision ID: 062_lpdp_breach_tracking
Revises: 061_lpdp_nis2_fw_versions
Create Date: 2026-04-05
"""
import sqlalchemy as sa
from alembic import op

revision = "062_lpdp_breach_tracking"
down_revision = "061_lpdp_nis2_fw_versions"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("data_breaches", sa.Column("poverenik_notified_at", sa.TIMESTAMP(timezone=True), nullable=True))
    op.add_column("data_breaches", sa.Column("poverenik_ref_number", sa.String(100), nullable=True))


def downgrade() -> None:
    op.drop_column("data_breaches", "poverenik_ref_number")
    op.drop_column("data_breaches", "poverenik_notified_at")
