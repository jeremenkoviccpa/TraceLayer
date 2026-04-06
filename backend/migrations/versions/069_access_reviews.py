"""Add access_reviews and access_review_items tables.

Revision ID: 069_access_reviews
Revises: 068_subprocessors
Create Date: 2026-04-06
"""
from alembic import op

revision = "069_access_reviews"
down_revision = "068_subprocessors"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("""
        CREATE TABLE IF NOT EXISTS access_reviews_v2 (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            company_id UUID NOT NULL REFERENCES companies(id) ON DELETE CASCADE,
            name VARCHAR(255) NOT NULL,
            framework VARCHAR(50) NOT NULL DEFAULT 'soc2',
            review_period VARCHAR(50) NOT NULL DEFAULT 'quarterly',
            status VARCHAR(50) NOT NULL DEFAULT 'in_progress',
            due_date TIMESTAMP WITH TIME ZONE,
            created_by_id UUID REFERENCES users(id) ON DELETE SET NULL,
            completed_at TIMESTAMP WITH TIME ZONE,
            created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
        )
    """)
    op.execute("CREATE INDEX IF NOT EXISTS ix_access_reviews_v2_company ON access_reviews_v2(company_id)")

    op.execute("""
        CREATE TABLE IF NOT EXISTS access_review_items (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            review_id UUID NOT NULL REFERENCES access_reviews_v2(id) ON DELETE CASCADE,
            user_email VARCHAR(255) NOT NULL,
            user_name VARCHAR(255),
            system_name VARCHAR(255) NOT NULL,
            role_or_permission VARCHAR(500),
            decision VARCHAR(50) NOT NULL DEFAULT 'pending',
            reviewed_by VARCHAR(255),
            reviewed_at TIMESTAMP WITH TIME ZONE,
            notes TEXT,
            created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
        )
    """)
    op.execute("CREATE INDEX IF NOT EXISTS ix_access_review_items_review ON access_review_items(review_id)")


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS access_review_items")
    op.execute("DROP TABLE IF EXISTS access_reviews_v2")
