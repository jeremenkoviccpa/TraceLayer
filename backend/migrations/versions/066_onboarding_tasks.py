"""Add onboarding_tasks table for automated new-hire onboarding workflow.

Revision ID: 066_onboarding_tasks
Revises: 065_ctrl_exclusions
Create Date: 2026-04-06
"""
from alembic import op

revision = "066_onboarding_tasks"
down_revision = "065_ctrl_exclusions"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("""
        CREATE TABLE IF NOT EXISTS onboarding_tasks (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            company_id UUID NOT NULL REFERENCES companies(id) ON DELETE CASCADE,
            employee_email VARCHAR(255) NOT NULL,
            employee_name VARCHAR(255),
            source VARCHAR(50) NOT NULL DEFAULT 'manual',
            hired_at TIMESTAMP WITH TIME ZONE,
            department VARCHAR(255),
            role_title VARCHAR(255),
            policy_ack_status VARCHAR(20) NOT NULL DEFAULT 'pending',
            training_status VARCHAR(20) NOT NULL DEFAULT 'pending',
            device_status VARCHAR(20) NOT NULL DEFAULT 'pending',
            background_check_status VARCHAR(20) NOT NULL DEFAULT 'pending',
            access_provisioned_status VARCHAR(20) NOT NULL DEFAULT 'pending',
            overall_status VARCHAR(20) NOT NULL DEFAULT 'in_progress',
            completed_at TIMESTAMP WITH TIME ZONE,
            notes TEXT,
            created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
            updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
            UNIQUE (company_id, employee_email)
        )
    """)
    op.execute("CREATE INDEX IF NOT EXISTS ix_onboarding_tasks_company ON onboarding_tasks(company_id)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_onboarding_tasks_status ON onboarding_tasks(company_id, overall_status)")


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS onboarding_tasks")
