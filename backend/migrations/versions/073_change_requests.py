"""Add change_requests table for SOC 2 CC8.1 change management.

Revision ID: 073_change_requests
Revises: 072_custom_frameworks
Create Date: 2026-04-06
"""
from alembic import op

revision = "073_change_requests"
down_revision = "072_custom_frameworks"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("""
        CREATE TABLE IF NOT EXISTS change_requests (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            company_id UUID NOT NULL REFERENCES companies(id) ON DELETE CASCADE,
            title VARCHAR(500) NOT NULL,
            description TEXT,
            change_type VARCHAR(100) NOT NULL DEFAULT 'code',
            risk_level VARCHAR(50) NOT NULL DEFAULT 'medium',
            status VARCHAR(50) NOT NULL DEFAULT 'draft',
            requester_name VARCHAR(255),
            requester_email VARCHAR(255),
            approver_name VARCHAR(255),
            approver_email VARCHAR(255),
            approved_at TIMESTAMP WITH TIME ZONE,
            rejected_at TIMESTAMP WITH TIME ZONE,
            rejection_reason TEXT,
            scheduled_at TIMESTAMP WITH TIME ZONE,
            deployed_at TIMESTAMP WITH TIME ZONE,
            closed_at TIMESTAMP WITH TIME ZONE,
            rollback_plan TEXT,
            ticket_url VARCHAR(1000),
            pr_url VARCHAR(1000),
            created_by_id UUID REFERENCES users(id) ON DELETE SET NULL,
            created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
            updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
        )
    """)
    op.execute("CREATE INDEX IF NOT EXISTS ix_change_requests_company ON change_requests(company_id)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_change_requests_company_status ON change_requests(company_id, status)")


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS change_requests")
