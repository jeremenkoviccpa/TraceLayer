"""Add devices, trust_page_views, questionnaire_sessions/comments, custom domain to trust_pages.

Revision ID: 043_add_gap_features
Revises: 042_add_partner_ecosystem
Create Date: 2026-03-23 00:00:00.000000
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = '043_add_gap_features'
down_revision = '042_add_partner_ecosystem'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ── Devices ───────────────────────────────────────────────────────────────
    op.create_table(
        'devices',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column('company_id', postgresql.UUID(as_uuid=True),
                  sa.ForeignKey('companies.id', ondelete='CASCADE'), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True),
                  sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
        sa.Column('device_name', sa.String(255), nullable=False),
        sa.Column('device_type', sa.String(50), nullable=False, server_default='laptop'),
        sa.Column('os_type', sa.String(50), nullable=False, server_default='macos'),
        sa.Column('os_version', sa.String(100), nullable=True),
        sa.Column('serial_number', sa.String(200), nullable=True),
        sa.Column('attested_by_email', sa.String(255), nullable=True),
        sa.Column('disk_encrypted', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('lockscreen_enabled', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('antivirus_installed', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('last_attested_at', sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.TIMESTAMP(timezone=True), server_default=sa.func.now()),
    )
    op.create_index('ix_devices_company_id', 'devices', ['company_id'])
    op.create_index('ix_devices_user_id', 'devices', ['user_id'])

    # ── Trust Page Views ──────────────────────────────────────────────────────
    op.create_table(
        'trust_page_views',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column('trust_page_id', postgresql.UUID(as_uuid=True),
                  sa.ForeignKey('trust_pages.id', ondelete='CASCADE'), nullable=False),
        sa.Column('company_id', postgresql.UUID(as_uuid=True),
                  sa.ForeignKey('companies.id', ondelete='CASCADE'), nullable=False),
        sa.Column('visitor_ip', sa.String(64), nullable=True),
        sa.Column('visitor_country', sa.String(2), nullable=True),
        sa.Column('referrer', sa.String(512), nullable=True),
        sa.Column('user_agent_summary', sa.String(200), nullable=True),
        sa.Column('viewed_at', sa.TIMESTAMP(timezone=True), server_default=sa.func.now()),
    )
    op.create_index('ix_trust_page_views_trust_page_id', 'trust_page_views', ['trust_page_id'])
    op.create_index('ix_trust_page_views_company_id', 'trust_page_views', ['company_id'])
    op.create_index('ix_trust_page_views_viewed_at', 'trust_page_views', ['viewed_at'])

    # ── Custom domain columns on trust_pages ──────────────────────────────────
    op.add_column('trust_pages', sa.Column('custom_domain', sa.String(253), nullable=True))
    op.add_column('trust_pages', sa.Column('domain_verified', sa.Boolean(), nullable=False, server_default='false'))
    op.add_column('trust_pages', sa.Column('domain_verification_token', sa.String(64), nullable=True))

    # ── Questionnaire Sessions ────────────────────────────────────────────────
    op.create_table(
        'questionnaire_sessions',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column('company_id', postgresql.UUID(as_uuid=True),
                  sa.ForeignKey('companies.id', ondelete='CASCADE'), nullable=False),
        sa.Column('created_by_id', postgresql.UUID(as_uuid=True),
                  sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
        sa.Column('assigned_to_id', postgresql.UUID(as_uuid=True),
                  sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
        sa.Column('title', sa.String(500), nullable=False),
        sa.Column('questionnaire_type', sa.String(50), nullable=True),
        sa.Column('status', sa.String(20), nullable=False, server_default='draft'),
        sa.Column('answers_json', sa.Text(), nullable=False, server_default='[]'),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.TIMESTAMP(timezone=True), server_default=sa.func.now()),
    )
    op.create_index('ix_questionnaire_sessions_company_id', 'questionnaire_sessions', ['company_id'])
    op.create_index('ix_questionnaire_sessions_assigned_to', 'questionnaire_sessions', ['assigned_to_id'])

    # ── Questionnaire Comments ────────────────────────────────────────────────
    op.create_table(
        'questionnaire_comments',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column('session_id', postgresql.UUID(as_uuid=True),
                  sa.ForeignKey('questionnaire_sessions.id', ondelete='CASCADE'), nullable=False),
        sa.Column('company_id', postgresql.UUID(as_uuid=True),
                  sa.ForeignKey('companies.id', ondelete='CASCADE'), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True),
                  sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
        sa.Column('user_email', sa.String(255), nullable=True),
        sa.Column('question_index', sa.Integer(), nullable=False),
        sa.Column('comment_text', sa.Text(), nullable=False),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.func.now()),
    )
    op.create_index('ix_questionnaire_comments_session_id', 'questionnaire_comments', ['session_id'])


def downgrade() -> None:
    op.drop_index('ix_questionnaire_comments_session_id', table_name='questionnaire_comments')
    op.drop_table('questionnaire_comments')
    op.drop_index('ix_questionnaire_sessions_assigned_to', table_name='questionnaire_sessions')
    op.drop_index('ix_questionnaire_sessions_company_id', table_name='questionnaire_sessions')
    op.drop_table('questionnaire_sessions')
    op.drop_column('trust_pages', 'domain_verification_token')
    op.drop_column('trust_pages', 'domain_verified')
    op.drop_column('trust_pages', 'custom_domain')
    op.drop_index('ix_trust_page_views_viewed_at', table_name='trust_page_views')
    op.drop_index('ix_trust_page_views_company_id', table_name='trust_page_views')
    op.drop_index('ix_trust_page_views_trust_page_id', table_name='trust_page_views')
    op.drop_table('trust_page_views')
    op.drop_index('ix_devices_user_id', table_name='devices')
    op.drop_index('ix_devices_company_id', table_name='devices')
    op.drop_table('devices')
