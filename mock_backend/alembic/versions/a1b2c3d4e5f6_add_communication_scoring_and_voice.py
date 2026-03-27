"""add communication scoring and voice embedding columns

Revision ID: a1b2c3d4e5f6
Revises: e9142a940e83
Create Date: 2026-03-26 21:56:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, Sequence[str], None] = 'e9142a940e83'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # CandidateProfile: add pyannote voice embedding column
    op.add_column('candidate_profiles', sa.Column('voice_embedding', sa.JSON(), nullable=True))

    # InterviewResponse: add communication scoring columns
    op.add_column('interview_responses', sa.Column('raw_transcript', sa.Text(), nullable=True))
    op.add_column('interview_responses', sa.Column('fluency_score', sa.Float(), nullable=True))
    op.add_column('interview_responses', sa.Column('prosody_score', sa.Float(), nullable=True))
    op.add_column('interview_responses', sa.Column('accuracy_score', sa.Float(), nullable=True))
    op.add_column('interview_responses', sa.Column('completeness_score', sa.Float(), nullable=True))
    op.add_column('interview_responses', sa.Column('pronunciation_score', sa.Float(), nullable=True))
    op.add_column('interview_responses', sa.Column('voice_verification_score', sa.Float(), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('interview_responses', 'voice_verification_score')
    op.drop_column('interview_responses', 'pronunciation_score')
    op.drop_column('interview_responses', 'completeness_score')
    op.drop_column('interview_responses', 'accuracy_score')
    op.drop_column('interview_responses', 'prosody_score')
    op.drop_column('interview_responses', 'fluency_score')
    op.drop_column('interview_responses', 'raw_transcript')
    op.drop_column('candidate_profiles', 'voice_embedding')
