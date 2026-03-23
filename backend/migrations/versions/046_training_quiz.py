"""Add quiz columns to training_records

Revision ID: 046_training_quiz
Revises: 045_audit_comments
Create Date: 2026-03-24
"""
from alembic import op
import sqlalchemy as sa

revision = "046_training_quiz"
down_revision = "045_audit_comments"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("training_records", sa.Column("completion_token", sa.String(64), nullable=True))
    op.add_column("training_records", sa.Column("quiz_score", sa.Integer(), nullable=True))
    op.add_column("training_records", sa.Column("quiz_passed", sa.Boolean(), server_default="false", nullable=False))
    op.add_column("training_records", sa.Column("quiz_attempts", sa.Integer(), server_default="0", nullable=False))
    op.create_unique_constraint("uq_training_completion_token", "training_records", ["completion_token"])
    op.create_index("ix_training_records_completion_token", "training_records", ["completion_token"])


def downgrade() -> None:
    op.drop_index("ix_training_records_completion_token", table_name="training_records")
    op.drop_constraint("uq_training_completion_token", "training_records", type_="unique")
    op.drop_column("training_records", "quiz_attempts")
    op.drop_column("training_records", "quiz_passed")
    op.drop_column("training_records", "quiz_score")
    op.drop_column("training_records", "completion_token")
