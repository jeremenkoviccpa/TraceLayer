"""Add launch gap features: incidents, assets, vulnerabilities, bcp_records,
background_checks, offboardings, notifications, and user 2FA fields.

Revision ID: 029_launch_gap_features
Revises: 029a_merge_heads
Create Date: 2026-03-18 00:00:00.000000
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = '029_launch_gap_features'
down_revision = '029a_merge_heads'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ── incidents ─────────────────────────────────────────────────────────────
    op.create_table(
        'incidents',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('company_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('companies.id', ondelete='CASCADE'), nullable=False),
        sa.Column('title', sa.String(255), nullable=False),
        sa.Column('description', sa.Text, nullable=True),
        sa.Column('severity', sa.String(50), nullable=False, server_default='medium'),
        sa.Column('status', sa.String(50), nullable=False, server_default='open'),
        sa.Column('detected_at', sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column('resolved_at', sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column('affected_systems', sa.Text, nullable=True),
        sa.Column('root_cause', sa.Text, nullable=True),
        sa.Column('lessons_learned', sa.Text, nullable=True),
        sa.Column('reporter_user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.TIMESTAMP(timezone=True), server_default=sa.func.now()),
    )
    op.create_index('ix_incidents_company_id', 'incidents', ['company_id'])

    # ── assets ────────────────────────────────────────────────────────────────
    op.create_table(
        'assets',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('company_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('companies.id', ondelete='CASCADE'), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('asset_type', sa.String(50), nullable=False, server_default='other'),
        sa.Column('owner_user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
        sa.Column('environment', sa.String(50), nullable=False, server_default='production'),
        sa.Column('classification', sa.String(50), nullable=False, server_default='internal'),
        sa.Column('status', sa.String(50), nullable=False, server_default='active'),
        sa.Column('vendor', sa.String(255), nullable=True),
        sa.Column('version', sa.String(100), nullable=True),
        sa.Column('ip_address', sa.String(100), nullable=True),
        sa.Column('location', sa.String(255), nullable=True),
        sa.Column('description', sa.Text, nullable=True),
        sa.Column('last_reviewed_at', sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.TIMESTAMP(timezone=True), server_default=sa.func.now()),
    )
    op.create_index('ix_assets_company_id', 'assets', ['company_id'])

    # ── vulnerabilities ───────────────────────────────────────────────────────
    op.create_table(
        'vulnerabilities',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('company_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('companies.id', ondelete='CASCADE'), nullable=False),
        sa.Column('title', sa.String(255), nullable=False),
        sa.Column('cve_id', sa.String(50), nullable=True),
        sa.Column('severity', sa.String(50), nullable=False, server_default='medium'),
        sa.Column('status', sa.String(50), nullable=False, server_default='open'),
        sa.Column('affected_system', sa.String(255), nullable=True),
        sa.Column('discovered_at', sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column('due_date', sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column('resolved_at', sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column('description', sa.Text, nullable=True),
        sa.Column('remediation_notes', sa.Text, nullable=True),
        sa.Column('owner_user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.TIMESTAMP(timezone=True), server_default=sa.func.now()),
    )
    op.create_index('ix_vulnerabilities_company_id', 'vulnerabilities', ['company_id'])

    # ── bcp_records ───────────────────────────────────────────────────────────
    op.create_table(
        'bcp_records',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('company_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('companies.id', ondelete='CASCADE'), nullable=False),
        sa.Column('title', sa.String(255), nullable=False),
        sa.Column('record_type', sa.String(50), nullable=False, server_default='both'),
        sa.Column('status', sa.String(50), nullable=False, server_default='not_tested'),
        sa.Column('last_tested_at', sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column('next_test_due', sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column('rto_minutes', sa.Integer, nullable=True),
        sa.Column('rpo_minutes', sa.Integer, nullable=True),
        sa.Column('test_results', sa.Text, nullable=True),
        sa.Column('scope', sa.Text, nullable=True),
        sa.Column('notes', sa.Text, nullable=True),
        sa.Column('owner_user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
        sa.Column('file_url', sa.String(1000), nullable=True),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.TIMESTAMP(timezone=True), server_default=sa.func.now()),
    )
    op.create_index('ix_bcp_records_company_id', 'bcp_records', ['company_id'])

    # ── background_checks ─────────────────────────────────────────────────────
    op.create_table(
        'background_checks',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('company_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('companies.id', ondelete='CASCADE'), nullable=False),
        sa.Column('employee_name', sa.String(255), nullable=False),
        sa.Column('employee_email', sa.String(255), nullable=True),
        sa.Column('check_type', sa.String(50), nullable=False, server_default='standard'),
        sa.Column('vendor', sa.String(255), nullable=True),
        sa.Column('status', sa.String(50), nullable=False, server_default='pending'),
        sa.Column('initiated_at', sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column('completed_at', sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column('valid_until', sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column('notes', sa.Text, nullable=True),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.TIMESTAMP(timezone=True), server_default=sa.func.now()),
    )
    op.create_index('ix_background_checks_company_id', 'background_checks', ['company_id'])

    # ── offboardings ──────────────────────────────────────────────────────────
    op.create_table(
        'offboardings',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('company_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('companies.id', ondelete='CASCADE'), nullable=False),
        sa.Column('employee_name', sa.String(255), nullable=False),
        sa.Column('employee_email', sa.String(255), nullable=True),
        sa.Column('last_day', sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column('department', sa.String(255), nullable=True),
        sa.Column('status', sa.String(50), nullable=False, server_default='pending'),
        sa.Column('checklist', postgresql.JSONB, nullable=False, server_default='[]'),
        sa.Column('completed_by_user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
        sa.Column('completed_at', sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column('notes', sa.Text, nullable=True),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.TIMESTAMP(timezone=True), server_default=sa.func.now()),
    )
    op.create_index('ix_offboardings_company_id', 'offboardings', ['company_id'])

    # ── notifications ─────────────────────────────────────────────────────────
    op.create_table(
        'notifications',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('company_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('companies.id', ondelete='CASCADE'), nullable=False),
        sa.Column('type', sa.String(50), nullable=False, server_default='info'),
        sa.Column('title', sa.String(255), nullable=False),
        sa.Column('message', sa.Text, nullable=False),
        sa.Column('read', sa.Boolean, nullable=False, server_default='false'),
        sa.Column('resource_type', sa.String(100), nullable=True),
        sa.Column('resource_id', sa.String(255), nullable=True),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.func.now()),
    )
    op.create_index('ix_notifications_user_id', 'notifications', ['user_id'])
    op.create_index('ix_notifications_user_unread', 'notifications', ['user_id', 'read'])

    # ── user 2FA fields ───────────────────────────────────────────────────────
    op.add_column('users', sa.Column('totp_secret_enc', sa.String(500), nullable=True))
    op.add_column('users', sa.Column('totp_enabled', sa.Boolean, nullable=False, server_default='false'))
    op.add_column('users', sa.Column('totp_backup_codes_enc', sa.Text, nullable=True))


def downgrade() -> None:
    op.drop_column('users', 'totp_backup_codes_enc')
    op.drop_column('users', 'totp_enabled')
    op.drop_column('users', 'totp_secret_enc')
    op.drop_index('ix_notifications_user_unread', table_name='notifications')
    op.drop_index('ix_notifications_user_id', table_name='notifications')
    op.drop_table('notifications')
    op.drop_index('ix_offboardings_company_id', table_name='offboardings')
    op.drop_table('offboardings')
    op.drop_index('ix_background_checks_company_id', table_name='background_checks')
    op.drop_table('background_checks')
    op.drop_index('ix_bcp_records_company_id', table_name='bcp_records')
    op.drop_table('bcp_records')
    op.drop_index('ix_vulnerabilities_company_id', table_name='vulnerabilities')
    op.drop_table('vulnerabilities')
    op.drop_index('ix_assets_company_id', table_name='assets')
    op.drop_table('assets')
    op.drop_index('ix_incidents_company_id', table_name='incidents')
    op.drop_table('incidents')
