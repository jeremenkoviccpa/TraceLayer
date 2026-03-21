"""Add auto_detected and detection_key to training_records and background_checks

Revision ID: 033_auto_training_bgcheck
Revises: 032_add_risk_auto_fields
Create Date: 2026-03-21 00:00:00.000000
"""
from alembic import op
import sqlalchemy as sa

revision = '033_auto_training_bgcheck'
down_revision = '032_add_risk_auto_fields'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Training records
    op.add_column('training_records', sa.Column('auto_detected', sa.Boolean(), nullable=False, server_default='false'))
    op.add_column('training_records', sa.Column('detection_key', sa.String(255), nullable=True))
    op.create_index('ix_training_records_detection_key', 'training_records', ['company_id', 'detection_key'])

    # Background checks
    op.add_column('background_checks', sa.Column('auto_detected', sa.Boolean(), nullable=False, server_default='false'))
    op.add_column('background_checks', sa.Column('detection_key', sa.String(255), nullable=True))
    op.create_index('ix_background_checks_detection_key', 'background_checks', ['company_id', 'detection_key'])


def downgrade() -> None:
    op.drop_index('ix_background_checks_detection_key', table_name='background_checks')
    op.drop_column('background_checks', 'detection_key')
    op.drop_column('background_checks', 'auto_detected')

    op.drop_index('ix_training_records_detection_key', table_name='training_records')
    op.drop_column('training_records', 'detection_key')
    op.drop_column('training_records', 'auto_detected')
