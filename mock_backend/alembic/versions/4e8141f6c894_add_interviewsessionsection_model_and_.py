"""Add InterviewSessionSection model and relations

Revision ID: 4e8141f6c894
Revises: d4e5f6a7b8c9
Create Date: 2026-03-06 00:51:28.090982

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect, text


# revision identifiers, used by Alembic.
revision: str = '4e8141f6c894'
down_revision: Union[str, Sequence[str], None] = 'd4e5f6a7b8c9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Use PostgreSQL DO blocks to handle errors gracefully and avoid transaction aborts
    from sqlalchemy import text
    
    # Create interview_session_sections table if it doesn't exist
    op.execute(text("""
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.tables 
                WHERE table_name = 'interview_session_sections'
            ) THEN
                CREATE TABLE interview_session_sections (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    interview_session_id UUID NOT NULL,
                    section_type VARCHAR(50) NOT NULL,
                    order_index INTEGER NOT NULL,
                    duration_minutes INTEGER NOT NULL,
                    status VARCHAR(20) NOT NULL DEFAULT 'pending',
                    started_at TIMESTAMP WITH TIME ZONE,
                    completed_at TIMESTAMP WITH TIME ZONE,
                    CONSTRAINT check_section_type CHECK (section_type IN ('technical', 'coding', 'conversational')),
                    CONSTRAINT check_section_status CHECK (status IN ('pending', 'in_progress', 'completed')),
                    CONSTRAINT fk_interview_session_sections_session 
                        FOREIGN KEY (interview_session_id) 
                        REFERENCES interview_sessions(id) 
                        ON DELETE CASCADE
                );
                CREATE INDEX ix_interview_session_sections_interview_session_id 
                    ON interview_session_sections(interview_session_id);
            END IF;
        EXCEPTION WHEN OTHERS THEN
            -- Table might already exist with different structure, ignore
            NULL;
        END $$;
    """))
    
    # Add interview_session_id column if it doesn't exist
    op.execute(text("""
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns 
                WHERE table_name = 'interview_session_questions' 
                AND column_name = 'interview_session_id'
            ) THEN
                -- Clear data first to avoid NOT NULL constraint issues
                DELETE FROM interview_session_questions;
                DELETE FROM interview_sessions;
                
                ALTER TABLE interview_session_questions 
                ADD COLUMN interview_session_id UUID;
                
                ALTER TABLE interview_session_questions 
                ALTER COLUMN interview_session_id SET NOT NULL;
            END IF;
        EXCEPTION WHEN OTHERS THEN
            -- Column might already exist, ignore
            NULL;
        END $$;
    """))
    
    # Add section_id column if it doesn't exist
    op.execute(text("""
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns 
                WHERE table_name = 'interview_session_questions' 
                AND column_name = 'section_id'
            ) THEN
                ALTER TABLE interview_session_questions 
                ADD COLUMN section_id UUID;
            END IF;
        EXCEPTION WHEN OTHERS THEN
            -- Column might already exist, ignore
            NULL;
        END $$;
    """))
    
    # Create indexes if they don't exist
    op.execute(text("""
        DO $$
        BEGIN
            -- Drop old index if it exists
            IF EXISTS (
                SELECT 1 FROM pg_indexes 
                WHERE tablename = 'interview_session_questions' 
                AND indexname = 'ix_interview_session_questions_interview_id'
            ) THEN
                DROP INDEX IF EXISTS ix_interview_session_questions_interview_id;
            END IF;
            
            -- Create new indexes
            IF NOT EXISTS (
                SELECT 1 FROM pg_indexes 
                WHERE tablename = 'interview_session_questions' 
                AND indexname = 'ix_interview_session_questions_interview_session_id'
            ) THEN
                CREATE INDEX ix_interview_session_questions_interview_session_id 
                    ON interview_session_questions(interview_session_id);
            END IF;
            
            IF NOT EXISTS (
                SELECT 1 FROM pg_indexes 
                WHERE tablename = 'interview_session_questions' 
                AND indexname = 'ix_interview_session_questions_section_id'
            ) THEN
                CREATE INDEX ix_interview_session_questions_section_id 
                    ON interview_session_questions(section_id);
            END IF;
            
            IF NOT EXISTS (
                SELECT 1 FROM pg_indexes 
                WHERE tablename = 'interview_session_questions' 
                AND indexname = 'idx_session_section_order'
            ) THEN
                CREATE INDEX idx_session_section_order 
                    ON interview_session_questions(interview_session_id, section_id, "order");
            END IF;
        EXCEPTION WHEN OTHERS THEN
            -- Indexes might already exist, ignore
            NULL;
        END $$;
    """))
    
    # Drop old foreign key and create new ones
    op.execute(text("""
        DO $$
        BEGIN
            -- Drop old foreign key if it exists
            IF EXISTS (
                SELECT 1 FROM information_schema.table_constraints 
                WHERE table_name = 'interview_session_questions' 
                AND constraint_name = 'interview_session_questions_interview_id_fkey'
            ) THEN
                ALTER TABLE interview_session_questions 
                DROP CONSTRAINT interview_session_questions_interview_id_fkey;
            END IF;
            
            -- Create new foreign keys if they don't exist
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.table_constraints 
                WHERE table_name = 'interview_session_questions' 
                AND constraint_name LIKE '%section_id%'
                AND constraint_type = 'FOREIGN KEY'
            ) THEN
                ALTER TABLE interview_session_questions 
                ADD CONSTRAINT fk_isq_section_id 
                    FOREIGN KEY (section_id) 
                    REFERENCES interview_session_sections(id) 
                    ON DELETE CASCADE;
            END IF;
            
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.table_constraints 
                WHERE table_name = 'interview_session_questions' 
                AND constraint_name LIKE '%interview_session_id%'
                AND constraint_type = 'FOREIGN KEY'
            ) THEN
                ALTER TABLE interview_session_questions 
                ADD CONSTRAINT fk_isq_interview_session_id 
                    FOREIGN KEY (interview_session_id) 
                    REFERENCES interview_sessions(id) 
                    ON DELETE CASCADE;
            END IF;
        EXCEPTION WHEN OTHERS THEN
            -- Constraints might already exist, ignore
            NULL;
        END $$;
    """))
    
    # Drop old interview_id column if it exists
    op.execute(text("""
        DO $$
        BEGIN
            IF EXISTS (
                SELECT 1 FROM information_schema.columns 
                WHERE table_name = 'interview_session_questions' 
                AND column_name = 'interview_id'
            ) THEN
                ALTER TABLE interview_session_questions 
                DROP COLUMN interview_id;
            END IF;
        EXCEPTION WHEN OTHERS THEN
            -- Column might not exist or has dependencies, ignore
            NULL;
        END $$;
    """))
    
    # Set section_id to NOT NULL (delete NULL values first)
    op.execute(text("""
        DO $$
        BEGIN
            -- First, delete any rows with NULL section_id
            DELETE FROM interview_session_questions WHERE section_id IS NULL;
            
            -- Then set column to NOT NULL if it's currently nullable
            IF EXISTS (
                SELECT 1 FROM information_schema.columns 
                WHERE table_name = 'interview_session_questions' 
                AND column_name = 'section_id'
                AND is_nullable = 'YES'
            ) THEN
                ALTER TABLE interview_session_questions 
                ALTER COLUMN section_id SET NOT NULL;
            END IF;
        EXCEPTION WHEN OTHERS THEN
            -- Column might already be NOT NULL or doesn't exist, ignore
            NULL;
        END $$;
    """))
    
    # Add current_section_id to interview_sessions if it doesn't exist
    op.execute(text("""
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns 
                WHERE table_name = 'interview_sessions' 
                AND column_name = 'current_section_id'
            ) THEN
                ALTER TABLE interview_sessions 
                ADD COLUMN current_section_id UUID;
                
                ALTER TABLE interview_sessions 
                ADD CONSTRAINT fk_interview_sessions_current_section_id 
                    FOREIGN KEY (current_section_id) 
                    REFERENCES interview_session_sections(id) 
                    ON DELETE SET NULL;
            END IF;
        EXCEPTION WHEN OTHERS THEN
            -- Column or constraint might already exist, ignore
            NULL;
        END $$;
    """))


def downgrade() -> None:
    """Downgrade schema."""
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint(None, 'interview_sessions', type_='foreignkey')
    op.drop_column('interview_sessions', 'current_section_id')
    op.add_column('interview_session_questions', sa.Column('interview_id', sa.UUID(), autoincrement=False, nullable=False))
    op.drop_constraint(None, 'interview_session_questions', type_='foreignkey')
    op.drop_constraint(None, 'interview_session_questions', type_='foreignkey')
    op.create_foreign_key(op.f('interview_session_questions_interview_id_fkey'), 'interview_session_questions', 'interviews', ['interview_id'], ['id'], ondelete='CASCADE')
    op.drop_index('idx_session_section_order', table_name='interview_session_questions')
    op.drop_index(op.f('ix_interview_session_questions_section_id'), table_name='interview_session_questions')
    op.drop_index(op.f('ix_interview_session_questions_interview_session_id'), table_name='interview_session_questions')
    op.create_index(op.f('ix_interview_session_questions_interview_id'), 'interview_session_questions', ['interview_id'], unique=False)
    op.drop_column('interview_session_questions', 'section_id')
    op.drop_column('interview_session_questions', 'interview_session_id')
    op.drop_index(op.f('ix_interview_session_sections_interview_session_id'), table_name='interview_session_sections')
    op.drop_table('interview_session_sections')
    # ### end Alembic commands ###
