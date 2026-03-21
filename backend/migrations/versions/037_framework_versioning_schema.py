"""Add framework versioning schema: framework_versions, framework_source_manifests,
control_mappings, framework_update_requests tables, and new columns on controls.

Revision ID: 037_framework_versioning_schema
Revises: 036_add_teams_webhook
Create Date: 2026-03-21 00:00:00.000000
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = '037_framework_versioning_schema'
down_revision = '036_add_teams_webhook'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ── framework_versions ────────────────────────────────────────────────────
    op.create_table(
        'framework_versions',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column('framework_key', sa.String(50), nullable=False),
        sa.Column('version', sa.String(50), nullable=False),
        sa.Column('display_name', sa.String(255), nullable=False),
        sa.Column('published_at', sa.Date(), nullable=True),
        sa.Column('is_current', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('deprecated_at', sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column('change_summary', sa.Text(), nullable=True),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.func.now()),
        sa.UniqueConstraint('framework_key', 'version', name='uq_framework_versions_key_version'),
    )
    op.create_index('ix_framework_versions_key', 'framework_versions', ['framework_key'])

    # ── framework_source_manifests ────────────────────────────────────────────
    op.create_table(
        'framework_source_manifests',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column('framework_key', sa.String(50), nullable=False, unique=True),
        sa.Column('source_url', sa.Text(), nullable=False),
        sa.Column('last_checked_at', sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column('last_hash', sa.String(64), nullable=True),
        sa.Column('current_version', sa.String(50), nullable=False),
        sa.Column('pending_update', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('pending_update_detected_at', sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.TIMESTAMP(timezone=True), server_default=sa.func.now()),
    )

    # ── control_mappings ──────────────────────────────────────────────────────
    op.create_table(
        'control_mappings',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column('from_control_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('controls.id', ondelete='CASCADE'), nullable=False),
        sa.Column('to_control_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('controls.id', ondelete='CASCADE'), nullable=False),
        sa.Column('relationship', sa.String(50), nullable=False),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.func.now()),
        sa.UniqueConstraint('from_control_id', 'to_control_id', name='uq_control_mappings_from_to'),
    )

    # ── framework_update_requests ─────────────────────────────────────────────
    op.create_table(
        'framework_update_requests',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column('framework_key', sa.String(50), nullable=False),
        sa.Column('detected_at', sa.TIMESTAMP(timezone=True), nullable=False),
        sa.Column('source_url', sa.Text(), nullable=False),
        sa.Column('new_hash', sa.String(64), nullable=False),
        sa.Column('old_hash', sa.String(64), nullable=True),
        sa.Column('ai_extraction_json', postgresql.JSONB(), nullable=True),
        sa.Column('status', sa.String(20), nullable=False, server_default='pending'),
        sa.Column('reviewed_by', sa.String(255), nullable=True),
        sa.Column('reviewed_at', sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column('review_notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.func.now()),
    )
    op.create_index('ix_framework_update_requests_status', 'framework_update_requests', ['status'])

    # ── ALTER TABLE controls ───────────────────────────────────────────────────
    op.add_column('controls', sa.Column('framework_version', sa.String(50), nullable=True))
    op.add_column('controls', sa.Column('deprecated_at', sa.TIMESTAMP(timezone=True), nullable=True))
    op.add_column('controls', sa.Column('external_id', sa.String(100), nullable=True))
    op.create_index('ix_controls_framework_version', 'controls', ['framework_version'])


def downgrade() -> None:
    op.drop_index('ix_controls_framework_version', table_name='controls')
    op.drop_column('controls', 'external_id')
    op.drop_column('controls', 'deprecated_at')
    op.drop_column('controls', 'framework_version')

    op.drop_index('ix_framework_update_requests_status', table_name='framework_update_requests')
    op.drop_table('framework_update_requests')

    op.drop_table('control_mappings')

    op.drop_table('framework_source_manifests')

    op.drop_index('ix_framework_versions_key', table_name='framework_versions')
    op.drop_table('framework_versions')
