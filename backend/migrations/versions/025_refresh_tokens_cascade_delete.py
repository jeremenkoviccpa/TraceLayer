"""Add ON DELETE CASCADE to refresh_tokens.user_id FK.

Revision ID: 025
Revises: 024
"""
import sqlalchemy as sa
from alembic import op

revision = "025"
down_revision = "024"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Drop the existing FK constraint, then re-add it with ON DELETE CASCADE
    op.drop_constraint("fk_refresh_tokens_user_id_users", "refresh_tokens", type_="foreignkey")
    op.create_foreign_key(
        "fk_refresh_tokens_user_id_users",
        "refresh_tokens",
        "users",
        ["user_id"],
        ["id"],
        ondelete="CASCADE",
    )


def downgrade() -> None:
    op.drop_constraint("fk_refresh_tokens_user_id_users", "refresh_tokens", type_="foreignkey")
    op.create_foreign_key(
        "fk_refresh_tokens_user_id_users",
        "refresh_tokens",
        "users",
        ["user_id"],
        ["id"],
    )
