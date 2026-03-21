"""Add control_status_snapshots and control_drift_events tables for compliance drift detection.

Revision ID: 039_control_drift_events
Revises: 038_seed_framework_versions
Create Date: 2026-03-21 00:00:00.000000
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = '039_control_drift_events'
down_revision = '038_seed_framework_versions'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ── control_status_snapshots ──────────────────────────────────────────────
    op.create_table(
        'control_status_snapshots',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column('company_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('companies.id', ondelete='CASCADE'), nullable=False),
        sa.Column('framework', sa.String(50), nullable=False),
        sa.Column('control_category', sa.String(100), nullable=False),
        sa.Column('status', sa.String(20), nullable=False),
        sa.Column('score', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('updated_at', sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint('company_id', 'framework', 'control_category', name='uq_control_status_snapshots'),
    )
    op.create_index('ix_control_status_snapshots_company', 'control_status_snapshots', ['company_id'])

    # ── control_drift_events ──────────────────────────────────────────────────
    op.create_table(
        'control_drift_events',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column('company_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('companies.id', ondelete='CASCADE'), nullable=False),
        sa.Column('framework', sa.String(50), nullable=False),
        sa.Column('control_category', sa.String(100), nullable=False),
        sa.Column('control_name', sa.String(255), nullable=False),
        sa.Column('previous_status', sa.String(20), nullable=False),
        sa.Column('new_status', sa.String(20), nullable=False),
        sa.Column('is_regression', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('trigger_integration', sa.String(100), nullable=True),
        sa.Column('detected_at', sa.TIMESTAMP(timezone=True), nullable=False),
        sa.Column('alerted_at', sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.func.now()),
    )
    op.create_index('ix_control_drift_events_company_detected', 'control_drift_events', ['company_id', 'detected_at'])


def downgrade() -> None:
    op.drop_index('ix_control_drift_events_company_detected', table_name='control_drift_events')
    op.drop_table('control_drift_events')

    op.drop_index('ix_control_status_snapshots_company', table_name='control_status_snapshots')
    op.drop_table('control_status_snapshots')
