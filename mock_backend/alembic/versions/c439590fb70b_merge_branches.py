"""merge branches

Revision ID: c439590fb70b
Revises: a1b2c3d4e5f6, c7f9d72d1e11
Create Date: 2026-03-26 23:45:00.657579

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c439590fb70b'
down_revision: Union[str, Sequence[str], None] = ('a1b2c3d4e5f6', 'c7f9d72d1e11')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
