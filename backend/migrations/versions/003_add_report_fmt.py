"""Add fmt column to reports

Revision ID: 003
Revises: 002
Create Date: 2024-01-03 00:00:00.000000
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "003"
down_revision: Union[str, None] = "002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "reports",
        sa.Column("fmt", sa.String(10), nullable=False, server_default="json"),
    )


def downgrade() -> None:
    op.drop_column("reports", "fmt")
