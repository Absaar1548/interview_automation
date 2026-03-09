"""
Create missing tables that are needed for the interview system to work.
This script checks what tables exist and creates the missing ones.
"""
import asyncio
import sys
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine
from app.core.config import settings

async def create_missing_tables():
    engine = create_async_engine(settings.DATABASE_URL, echo=False)
    try:
        async with engine.begin() as conn:
            print("Checking and creating missing tables...")
            
            # Check if coding_problems table exists
            result = await conn.execute(text("""
                SELECT EXISTS (
                    SELECT 1 FROM information_schema.tables 
                    WHERE table_name = 'coding_problems'
                )
            """))
            coding_problems_exists = result.scalar()
            
            if not coding_problems_exists:
                print("Creating coding_problems table...")
                await conn.execute(text("""
                    CREATE TABLE coding_problems (
                        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                        question_id UUID NOT NULL,
                        title VARCHAR NOT NULL,
                        description TEXT NOT NULL,
                        difficulty VARCHAR NOT NULL,
                        starter_code JSONB,
                        time_limit_sec INTEGER NOT NULL DEFAULT 900,
                        created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
                        CONSTRAINT fk_coding_problems_question 
                            FOREIGN KEY (question_id) 
                            REFERENCES questions(id) 
                            ON DELETE CASCADE,
                        CONSTRAINT uq_coding_problems_question_id UNIQUE (question_id)
                    )
                """))
                print("✓ Created coding_problems table")
            else:
                print("✓ coding_problems table already exists")
            
            # Check if interview_session_sections table exists
            result = await conn.execute(text("""
                SELECT EXISTS (
                    SELECT 1 FROM information_schema.tables 
                    WHERE table_name = 'interview_session_sections'
                )
            """))
            sections_exists = result.scalar()
            
            if not sections_exists:
                print("Creating interview_session_sections table...")
                await conn.execute(text("""
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
                    )
                """))
                await conn.execute(text("""
                    CREATE INDEX ix_interview_session_sections_interview_session_id 
                        ON interview_session_sections(interview_session_id)
                """))
                print("✓ Created interview_session_sections table")
            else:
                print("✓ interview_session_sections table already exists")
            
            # Check if interview_session_questions has interview_session_id column
            result = await conn.execute(text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'interview_session_questions' AND column_name = 'interview_session_id'
            """))
            session_id_col_exists = result.fetchone() is not None
            
            if not session_id_col_exists:
                print("Adding interview_session_id column to interview_session_questions...")
                await conn.execute(text("""
                    ALTER TABLE interview_session_questions 
                    ADD COLUMN interview_session_id UUID
                """))
                # Set a default value for existing rows (if any)
                # Then make it NOT NULL
                await conn.execute(text("""
                    UPDATE interview_session_questions 
                    SET interview_session_id = (
                        SELECT id FROM interview_sessions LIMIT 1
                    )
                    WHERE interview_session_id IS NULL
                """))
                await conn.execute(text("""
                    ALTER TABLE interview_session_questions 
                    ALTER COLUMN interview_session_id SET NOT NULL
                """))
                await conn.execute(text("""
                    ALTER TABLE interview_session_questions 
                    ADD CONSTRAINT fk_isq_interview_session_id 
                        FOREIGN KEY (interview_session_id) 
                        REFERENCES interview_sessions(id) 
                        ON DELETE CASCADE
                """))
                await conn.execute(text("""
                    CREATE INDEX ix_interview_session_questions_interview_session_id 
                        ON interview_session_questions(interview_session_id)
                """))
                print("✓ Added interview_session_id column")
            else:
                print("✓ interview_session_id column already exists")
            
            # Check if interview_session_questions has section_id column
            result = await conn.execute(text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'interview_session_questions' AND column_name = 'section_id'
            """))
            section_id_col_exists = result.fetchone() is not None
            
            if not section_id_col_exists:
                print("Adding section_id column to interview_session_questions...")
                await conn.execute(text("""
                    ALTER TABLE interview_session_questions 
                    ADD COLUMN section_id UUID
                """))
                await conn.execute(text("""
                    ALTER TABLE interview_session_questions 
                    ADD CONSTRAINT fk_isq_section_id 
                        FOREIGN KEY (section_id) 
                        REFERENCES interview_session_sections(id) 
                        ON DELETE CASCADE
                """))
                await conn.execute(text("""
                    CREATE INDEX ix_interview_session_questions_section_id 
                        ON interview_session_questions(section_id)
                """))
                print("✓ Added section_id column")
            else:
                print("✓ section_id column already exists")
            
            print("\n✓ All required tables and columns are in place!")
                
    except Exception as e:
        print(f"✗ Error creating missing tables: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        await engine.dispose()

if __name__ == "__main__":
    asyncio.run(create_missing_tables())
