"""Add PCI DSS, GDPR, and ISO 42001 certification columns to vendors table.

Revision ID: 077_vendor_certs
Revises: 076_full_fw_coverage
Create Date: 2026-04-06
"""

import sqlalchemy as sa
from alembic import op

revision = "077_vendor_certs"
down_revision = "076_full_fw_coverage"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("vendors", sa.Column("pci_dss_certified",  sa.Boolean(), nullable=False, server_default="false"))
    op.add_column("vendors", sa.Column("gdpr_certified",     sa.Boolean(), nullable=False, server_default="false"))
    op.add_column("vendors", sa.Column("iso42001_certified", sa.Boolean(), nullable=False, server_default="false"))


def downgrade() -> None:
    op.drop_column("vendors", "iso42001_certified")
    op.drop_column("vendors", "gdpr_certified")
    op.drop_column("vendors", "pci_dss_certified")
