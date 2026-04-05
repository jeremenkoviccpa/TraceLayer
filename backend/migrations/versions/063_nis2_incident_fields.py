"""Add NIS2 3-stage incident reporting fields to incidents table.

NIS2 Art. 23 requires significant incidents to be reported in three stages:
  - Early warning: within 24 hours (nis2_early_warning_at)
  - Incident notification: within 72 hours (nis2_notified_at)
  - Final report: within 1 month (nis2_final_report_at)
  - CSIRT reference number (nis2_ref_number)

Revision ID: 063_nis2_incident_fields
Revises: 062_lpdp_breach_tracking
Create Date: 2026-04-05
"""
import sqlalchemy as sa
from alembic import op

revision = "063_nis2_incident_fields"
down_revision = "062_lpdp_breach_tracking"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("incidents", sa.Column("nis2_early_warning_at", sa.TIMESTAMP(timezone=True), nullable=True))
    op.add_column("incidents", sa.Column("nis2_notified_at", sa.TIMESTAMP(timezone=True), nullable=True))
    op.add_column("incidents", sa.Column("nis2_final_report_at", sa.TIMESTAMP(timezone=True), nullable=True))
    op.add_column("incidents", sa.Column("nis2_ref_number", sa.String(100), nullable=True))


def downgrade() -> None:
    op.drop_column("incidents", "nis2_ref_number")
    op.drop_column("incidents", "nis2_final_report_at")
    op.drop_column("incidents", "nis2_notified_at")
    op.drop_column("incidents", "nis2_early_warning_at")
