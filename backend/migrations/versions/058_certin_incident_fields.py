"""CERT-In production readiness: 6-hour incident reporting fields on incidents.

Adds certin_reported_at and certin_ref_number to the incidents table so that
companies can track their 6-hour CERT-In reporting obligation per Dir. 1
of the CERT-In Cybersecurity Directions 2022.

Revision ID: 058_certin_incident_fields
Revises: 057_dpdp_production_ready
Create Date: 2026-03-30
"""
import sqlalchemy as sa
from alembic import op

revision = "058_certin_incident_fields"
down_revision = "057_dpdp_production_ready"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "incidents",
        sa.Column("certin_reported_at", sa.TIMESTAMP(timezone=True), nullable=True),
    )
    op.add_column(
        "incidents",
        sa.Column("certin_ref_number", sa.String(100), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("incidents", "certin_ref_number")
    op.drop_column("incidents", "certin_reported_at")
