"""add question_type to questions

Revision ID: a1b2c3d4e5f6
Revises: 66ed4b635ed8
Create Date: 2026-03-05 14:52:46.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import text


# revision identifiers, used by Alembic.
revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, Sequence[str], None] = '66ed4b635ed8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# Define the enum type
questiontype_enum = sa.Enum('technical', 'behavioral', 'coding', name='questiontype')


def upgrade() -> None:
    """Add question_type enum and column to questions table."""
    # Create the enum type in the database
    questiontype_enum.create(op.get_bind(), checkfirst=True)

    # Check if column already exists using a DO block to handle transaction errors
    connection = op.get_bind()
    try:
        # Use a DO block to check and add column atomically
        connection.execute(text("""
            DO $$
            BEGIN
                IF NOT EXISTS (
                    SELECT 1 FROM information_schema.columns 
                    WHERE table_name = 'questions' AND column_name = 'question_type'
                ) THEN
                    ALTER TABLE questions ADD COLUMN question_type questiontype DEFAULT 'technical' NOT NULL;
                END IF;
            EXCEPTION WHEN duplicate_column THEN
                -- Column already exists, ignore
                NULL;
            WHEN OTHERS THEN
                -- Other error, re-raise
                RAISE;
            END $$;
        """))
    except Exception as e:
        # If the DO block fails, try the standard approach
        # This handles the case where the column might already exist
        try:
            op.add_column(
                'questions',
                sa.Column(
                    'question_type',
                    sa.Enum('technical', 'behavioral', 'coding', name='questiontype'),
                    nullable=False,
                    server_default='technical'
                )
            )
        except Exception:
            # Column already exists, that's fine
            pass


def downgrade() -> None:
    """Remove question_type column and enum from questions table."""
    # Drop the column first
    op.drop_column('questions', 'question_type')

    # Drop the enum type
    questiontype_enum.drop(op.get_bind(), checkfirst=True)
