"""add candidate_feedback column to interviews

Revision ID: c7f9d72d1e11
Revises: 933d04d2d5f1
Create Date: 2026-03-26 12:00:00.000000
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "c7f9d72d1e11"
down_revision = "933d04d2d5f1"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("interviews", sa.Column("candidate_feedback", sa.JSON(), nullable=True))


def downgrade() -> None:
    op.drop_column("interviews", "candidate_feedback")

