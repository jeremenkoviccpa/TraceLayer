"""Add compliance docs: soa_items, ropa_records, data_breaches, subject_requests, management_reviews

Revision ID: 030_compliance_docs
Revises: 029_launch_gap_features
Create Date: 2026-03-18 12:00:00.000000
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = '030_compliance_docs'
down_revision = '029_launch_gap_features'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'soa_items',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('company_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('annex_ref', sa.String(20), nullable=False),
        sa.Column('annex_theme', sa.String(50), nullable=False),
        sa.Column('title', sa.String(300), nullable=False),
        sa.Column('included', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('justification', sa.Text(), nullable=True),
        sa.Column('implementation_status', sa.String(50), nullable=False, server_default='not_started'),
        sa.Column('implementation_notes', sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(['company_id'], ['companies.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_soa_items_company_id', 'soa_items', ['company_id'])

    op.create_table(
        'ropa_records',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('company_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('name', sa.String(300), nullable=False),
        sa.Column('role', sa.String(50), nullable=False, server_default='controller'),
        sa.Column('purpose', sa.Text(), nullable=True),
        sa.Column('legal_basis', sa.String(100), nullable=True),
        sa.Column('data_categories', sa.Text(), nullable=True),
        sa.Column('data_subjects', sa.Text(), nullable=True),
        sa.Column('recipients', sa.Text(), nullable=True),
        sa.Column('third_country_transfers', sa.Text(), nullable=True),
        sa.Column('retention_period', sa.String(200), nullable=True),
        sa.Column('security_measures', sa.Text(), nullable=True),
        sa.Column('dpa_url', sa.Text(), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(['company_id'], ['companies.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_ropa_records_company_id', 'ropa_records', ['company_id'])

    op.create_table(
        'data_breaches',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('company_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('title', sa.String(300), nullable=False),
        sa.Column('occurred_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('discovered_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('breach_type', sa.String(50), nullable=False, server_default='confidentiality'),
        sa.Column('severity', sa.String(20), nullable=False, server_default='medium'),
        sa.Column('status', sa.String(50), nullable=False, server_default='investigating'),
        sa.Column('affected_records', sa.Integer(), nullable=True),
        sa.Column('affected_systems', sa.Text(), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('notification_required', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('dpa_notified_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('individuals_notified_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('root_cause', sa.Text(), nullable=True),
        sa.Column('remediation', sa.Text(), nullable=True),
        sa.Column('reporter_name', sa.String(200), nullable=True),
        sa.ForeignKeyConstraint(['company_id'], ['companies.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_data_breaches_company_id', 'data_breaches', ['company_id'])

    op.create_table(
        'subject_requests',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('company_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('requester_name', sa.String(200), nullable=False),
        sa.Column('requester_email', sa.String(200), nullable=True),
        sa.Column('request_type', sa.String(50), nullable=False),
        sa.Column('received_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('due_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('status', sa.String(50), nullable=False, server_default='pending'),
        sa.Column('response_notes', sa.Text(), nullable=True),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('regulation', sa.String(20), nullable=False, server_default='gdpr'),
        sa.ForeignKeyConstraint(['company_id'], ['companies.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_subject_requests_company_id', 'subject_requests', ['company_id'])

    op.create_table(
        'management_reviews',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('company_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('review_date', sa.DateTime(timezone=True), nullable=False),
        sa.Column('attendees', sa.Text(), nullable=True),
        sa.Column('inputs_summary', sa.Text(), nullable=True),
        sa.Column('decisions', sa.Text(), nullable=True),
        sa.Column('action_items', postgresql.JSONB(), nullable=False, server_default='[]'),
        sa.Column('next_review_date', sa.DateTime(timezone=True), nullable=True),
        sa.Column('outcome', sa.String(50), nullable=False, server_default='satisfactory'),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(['company_id'], ['companies.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_management_reviews_company_id', 'management_reviews', ['company_id'])


def downgrade() -> None:
    op.drop_index('ix_management_reviews_company_id', table_name='management_reviews')
    op.drop_table('management_reviews')
    op.drop_index('ix_subject_requests_company_id', table_name='subject_requests')
    op.drop_table('subject_requests')
    op.drop_index('ix_data_breaches_company_id', table_name='data_breaches')
    op.drop_table('data_breaches')
    op.drop_index('ix_ropa_records_company_id', table_name='ropa_records')
    op.drop_table('ropa_records')
    op.drop_index('ix_soa_items_company_id', table_name='soa_items')
    op.drop_table('soa_items')
