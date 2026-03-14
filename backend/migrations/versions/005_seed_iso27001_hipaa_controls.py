"""Seed ISO 27001 and HIPAA controls

Revision ID: 005
Revises: 004
Create Date: 2024-01-05 00:00:00.000000
"""
from typing import Sequence, Union
import uuid

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "005"
down_revision: Union[str, None] = "004"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

CONTROLS = [
    # ── ISO 27001 ───────────────────────────────────────────────────────────
    {
        "id": uuid.UUID("00000000-0000-0000-0001-000000000001"),
        "name": "Access Control (A.9)",
        "framework": "iso27001",
        "category": "access_control",
        "description": "Business requirements for access control, user access management, system and application access control.",
    },
    {
        "id": uuid.UUID("00000000-0000-0000-0001-000000000002"),
        "name": "Operations Security (A.12)",
        "framework": "iso27001",
        "category": "operations_security",
        "description": "Operational procedures, protection from malware, backup, logging, monitoring and control of operational software.",
    },
    {
        "id": uuid.UUID("00000000-0000-0000-0001-000000000003"),
        "name": "Communications Security (A.13)",
        "framework": "iso27001",
        "category": "communications_security",
        "description": "Network security management and information transfer policies and procedures.",
    },
    {
        "id": uuid.UUID("00000000-0000-0000-0001-000000000004"),
        "name": "System Acquisition & Change Control (A.14)",
        "framework": "iso27001",
        "category": "change_management",
        "description": "Security requirements for information systems, secure development and support processes.",
    },
    # ── HIPAA ───────────────────────────────────────────────────────────────
    {
        "id": uuid.UUID("00000000-0000-0000-0002-000000000001"),
        "name": "Access Control (§164.312(a))",
        "framework": "hipaa",
        "category": "access_control",
        "description": "Implement technical policies and procedures to allow only authorized persons to access ePHI.",
    },
    {
        "id": uuid.UUID("00000000-0000-0000-0002-000000000002"),
        "name": "Audit Controls (§164.312(b))",
        "framework": "hipaa",
        "category": "audit_controls",
        "description": "Implement hardware, software, and procedural mechanisms to record and examine activity in systems containing ePHI.",
    },
    {
        "id": uuid.UUID("00000000-0000-0000-0002-000000000003"),
        "name": "Workforce Security (§164.308(a)(3))",
        "framework": "hipaa",
        "category": "workforce_security",
        "description": "Implement policies to ensure all workforce members have appropriate access to ePHI.",
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
    op.bulk_insert(controls_table, CONTROLS)


def downgrade() -> None:
    ids = ", ".join(f"'{c['id']}'" for c in CONTROLS)
    op.execute(f"DELETE FROM controls WHERE id IN ({ids})")
