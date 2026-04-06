"""Add subprocessors table for GDPR/privacy subprocessor management.

Revision ID: 068_subprocessors
Revises: 067_vendor_questnrs
Create Date: 2026-04-06
"""
from alembic import op

revision = "068_subprocessors"
down_revision = "067_vendor_questnrs"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("""
        CREATE TABLE IF NOT EXISTS subprocessors (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            company_id UUID NOT NULL REFERENCES companies(id) ON DELETE CASCADE,
            name VARCHAR(255) NOT NULL,
            country VARCHAR(100),
            purpose TEXT,
            data_categories JSONB NOT NULL DEFAULT '[]',
            legal_basis VARCHAR(100),
            transfer_mechanism VARCHAR(100),
            dpa_signed BOOLEAN NOT NULL DEFAULT FALSE,
            dpa_signed_at TIMESTAMP WITH TIME ZONE,
            website VARCHAR(500),
            contact_email VARCHAR(255),
            created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
            updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now()
        )
    """)
    op.execute("CREATE INDEX IF NOT EXISTS ix_subprocessors_company ON subprocessors(company_id)")


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS subprocessors")
