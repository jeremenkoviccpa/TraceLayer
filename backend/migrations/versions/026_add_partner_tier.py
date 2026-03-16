"""Add partner tier: is_partner_account + partner_id on companies, partner_client_payments table.

Revision ID: 026
Revises: 025
"""
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "026"
down_revision = "025"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add partner columns to companies
    op.add_column("companies", sa.Column("is_partner_account", sa.Boolean(), nullable=False, server_default="false"))
    op.add_column("companies", sa.Column("partner_id", postgresql.UUID(as_uuid=True), nullable=True))
    op.create_foreign_key(
        "fk_companies_partner_id",
        "companies", "companies",
        ["partner_id"], ["id"],
        ondelete="SET NULL",
    )
    op.create_index("ix_companies_partner_id", "companies", ["partner_id"])

    # Partner client payments table
    op.create_table(
        "partner_client_payments",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("partner_company_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("companies.id", ondelete="CASCADE"), nullable=False),
        sa.Column("client_company_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("companies.id", ondelete="SET NULL"), nullable=True),
        sa.Column("ls_order_id", sa.Text(), nullable=True, unique=True),
        sa.Column("ls_checkout_id", sa.Text(), nullable=True),
        sa.Column("amount_cents", sa.Integer(), nullable=False, server_default="9900"),
        sa.Column("status", sa.String(50), nullable=False, server_default="pending"),
        sa.Column("client_name", sa.Text(), nullable=False),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), server_default=sa.func.now()),
        sa.Column("paid_at", sa.TIMESTAMP(timezone=True), nullable=True),
    )
    op.create_index("ix_partner_client_payments_partner_company_id", "partner_client_payments", ["partner_company_id"])


def downgrade() -> None:
    op.drop_table("partner_client_payments")
    op.drop_index("ix_companies_partner_id", "companies")
    op.drop_constraint("fk_companies_partner_id", "companies", type_="foreignkey")
    op.drop_column("companies", "partner_id")
    op.drop_column("companies", "is_partner_account")
