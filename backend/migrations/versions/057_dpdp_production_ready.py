"""DPDP production readiness: DPBI breach notification fields on data_breaches.

Adds dpbi_notified_at and dpbi_ref_number to the data_breaches table so that
companies can track their 72-hour DPBI (Data Protection Board of India)
notification obligation separately from the generic DPA notification field.

Revision ID: 057_dpdp_production_ready
Revises: 056_add_control_due_date
Create Date: 2026-03-30
"""
import sqlalchemy as sa
from alembic import op

revision = "057_dpdp_production_ready"
down_revision = "056_add_control_due_date"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "data_breaches",
        sa.Column("dpbi_notified_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "data_breaches",
        sa.Column("dpbi_ref_number", sa.String(100), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("data_breaches", "dpbi_ref_number")
    op.drop_column("data_breaches", "dpbi_notified_at")
