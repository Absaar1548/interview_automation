"""
Quick fix script to add current_section_id column to interview_sessions table.
Run this if the migration hasn't been applied yet.
"""

import asyncio
import sys
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine
from app.core.config import settings

async def fix_current_section_id():
    engine = create_async_engine(settings.DATABASE_URL, echo=False)
    try:
        async with engine.begin() as conn:
            print("Checking and adding current_section_id column to interview_sessions...")
            fix_sql = """
            DO $$
            BEGIN
                -- Add current_section_id column if it doesn't exist
                IF NOT EXISTS (
                    SELECT 1 FROM information_schema.columns 
                    WHERE table_name = 'interview_sessions' AND column_name = 'current_section_id'
                ) THEN
                    -- First check if interview_session_sections table exists
                    IF EXISTS (
                        SELECT 1 FROM information_schema.tables 
                        WHERE table_name = 'interview_session_sections'
                    ) THEN
                        ALTER TABLE interview_sessions 
                        ADD COLUMN current_section_id UUID 
                        REFERENCES interview_session_sections(id) ON DELETE SET NULL;
                        RAISE NOTICE 'Added column: interview_sessions.current_section_id';
                    ELSE
                        -- If sections table doesn't exist, add column without foreign key
                        ALTER TABLE interview_sessions 
                        ADD COLUMN current_section_id UUID;
                        RAISE NOTICE 'Added column: interview_sessions.current_section_id (without FK - sections table not found)';
                    END IF;
                ELSE
                    RAISE NOTICE 'Column interview_sessions.current_section_id already exists';
                END IF;
            END $$;
            """
            await conn.execute(text(fix_sql))
            print("✓ Successfully added current_section_id column to interview_sessions!")
    except Exception as e:
        print(f"✗ Error fixing interview_sessions schema: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        await engine.dispose()

if __name__ == "__main__":
    asyncio.run(fix_current_section_id())
