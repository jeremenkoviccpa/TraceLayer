"""Add onboarding_completed to companies.

Revision ID: 024
Revises: 023
"""
import sqlalchemy as sa
from alembic import op

revision = "024"
down_revision = "023"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "companies",
        sa.Column(
            "onboarding_completed",
            sa.Boolean,
            nullable=False,
            server_default=sa.text("true"),
        ),
    )


def downgrade() -> None:
    op.drop_column("companies", "onboarding_completed")
