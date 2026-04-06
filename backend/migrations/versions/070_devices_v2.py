"""Add devices_v2 table for endpoint security tracking.

Revision ID: 070_devices_v2
Revises: 069_access_reviews
Create Date: 2026-04-06
"""
from alembic import op

revision = "070_devices_v2"
down_revision = "069_access_reviews"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("""
        CREATE TABLE IF NOT EXISTS devices_v2 (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            company_id UUID NOT NULL REFERENCES companies(id) ON DELETE CASCADE,
            employee_email VARCHAR(255),
            employee_name VARCHAR(255),
            hostname VARCHAR(255),
            serial_number VARCHAR(255),
            os_type VARCHAR(50),
            os_version VARCHAR(100),
            disk_encryption BOOLEAN NOT NULL DEFAULT FALSE,
            screen_lock BOOLEAN NOT NULL DEFAULT FALSE,
            mdm_enrolled BOOLEAN NOT NULL DEFAULT FALSE,
            mdm_platform VARCHAR(100),
            last_seen_at TIMESTAMP WITH TIME ZONE,
            status VARCHAR(50) NOT NULL DEFAULT 'unknown',
            notes TEXT,
            created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
            updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
        )
    """)
    op.execute("CREATE INDEX IF NOT EXISTS ix_devices_v2_company ON devices_v2(company_id)")


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS devices_v2")
