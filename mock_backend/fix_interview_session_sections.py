"""
Quick fix script to create interview_session_sections table if it doesn't exist.
Run this if the migration hasn't been applied yet.
"""
import asyncio
import sys
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine
from app.core.config import settings

async def create_interview_session_sections_table():
    engine = create_async_engine(settings.DATABASE_URL, echo=False)
    try:
        async with engine.begin() as conn:
            print("Checking and creating 'interview_session_sections' table...")
            fix_sql = """
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
                    
                    RAISE NOTICE 'Created table: interview_session_sections';
                ELSE
                    RAISE NOTICE 'Table interview_session_sections already exists';
                END IF;
            END $$;
            """
            await conn.execute(text(fix_sql))
            print("✓ Successfully ensured 'interview_session_sections' table exists!")
    except Exception as e:
        print(f"✗ Error creating 'interview_session_sections' table: {e}")
        sys.exit(1)
    finally:
        await engine.dispose()

if __name__ == "__main__":
    asyncio.run(create_interview_session_sections_table())
