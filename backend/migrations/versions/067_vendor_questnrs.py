"""Add vendor_questionnaires table for outbound TPRM security questionnaires.

Revision ID: 067_vendor_questnrs
Revises: 066_onboarding_tasks
Create Date: 2026-04-06
"""
from alembic import op

revision = "067_vendor_questnrs"
down_revision = "066_onboarding_tasks"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("""
        CREATE TABLE IF NOT EXISTS vendor_questionnaires (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            company_id UUID NOT NULL REFERENCES companies(id) ON DELETE CASCADE,
            vendor_id UUID REFERENCES vendors(id) ON DELETE SET NULL,
            vendor_name VARCHAR(255) NOT NULL,
            sent_to_email VARCHAR(255) NOT NULL,
            token VARCHAR(64) NOT NULL UNIQUE,
            status VARCHAR(20) NOT NULL DEFAULT 'sent',
            questions JSONB NOT NULL DEFAULT '[]',
            responses JSONB NOT NULL DEFAULT '{}',
            sent_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
            due_date TIMESTAMP WITH TIME ZONE,
            completed_at TIMESTAMP WITH TIME ZONE,
            created_by_id UUID REFERENCES users(id) ON DELETE SET NULL,
            created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now()
        )
    """)
    op.execute("CREATE INDEX IF NOT EXISTS ix_vendor_questnrs_company ON vendor_questionnaires(company_id)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_vendor_questnrs_token ON vendor_questionnaires(token)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_vendor_questnrs_vendor ON vendor_questionnaires(vendor_id)")


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS vendor_questionnaires")
