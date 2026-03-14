"""Seed SOC 2 controls

Revision ID: 004
Revises: 003
Create Date: 2024-01-04 00:00:00.000000
"""
from typing import Sequence, Union
import uuid

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "004"
down_revision: Union[str, None] = "003"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

SOC2_CONTROLS = [
    {
        "id": uuid.UUID("00000000-0000-0000-0000-000000000001"),
        "name": "Access Control",
        "framework": "soc2",
        "category": "access_control",
        "description": "Controls to manage who has access to systems and data, including user provisioning, IAM policies, and privileged access.",
    },
    {
        "id": uuid.UUID("00000000-0000-0000-0000-000000000002"),
        "name": "Logging & Monitoring",
        "framework": "soc2",
        "category": "logging_monitoring",
        "description": "Controls to ensure system activity is logged and monitored, including audit trails and alerting.",
    },
    {
        "id": uuid.UUID("00000000-0000-0000-0000-000000000003"),
        "name": "Change Management",
        "framework": "soc2",
        "category": "change_management",
        "description": "Controls to manage changes to systems and code, including version control and deployment procedures.",
    },
]


def upgrade() -> None:
    controls_table = sa.table(
        "controls",
        sa.column("id", postgresql.UUID(as_uuid=True)),
        sa.column("name", sa.String),
        sa.column("framework", sa.String),
        sa.column("category", sa.String),
        sa.column("description", sa.Text),
    )
    op.bulk_insert(controls_table, SOC2_CONTROLS)


def downgrade() -> None:
    op.execute(
        "DELETE FROM controls WHERE framework = 'soc2' AND id IN ('00000000-0000-0000-0000-000000000001','00000000-0000-0000-0000-000000000002','00000000-0000-0000-0000-000000000003')"
    )
