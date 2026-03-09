"""
Quick fix script to add missing question_type column to questions table.
Run this if migrations haven't been applied yet.
"""

import asyncio
import sys
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine
from app.core.config import settings

async def fix_question_type_column():
    engine = create_async_engine(settings.DATABASE_URL, echo=False)
    try:
        async with engine.begin() as conn:
            print("Checking and adding missing question_type column to questions table...")
            fix_sql = """
            DO $$
            BEGIN
                -- Check if question_type column exists
                IF NOT EXISTS (
                    SELECT 1 FROM information_schema.columns 
                    WHERE table_name = 'questions' AND column_name = 'question_type'
                ) THEN
                    -- Create the enum type if it doesn't exist
                    IF NOT EXISTS (
                        SELECT 1 FROM pg_type WHERE typname = 'questiontype'
                    ) THEN
                        CREATE TYPE questiontype AS ENUM ('technical', 'behavioral', 'coding');
                    END IF;
                    
                    -- Add the column with default value
                    ALTER TABLE questions ADD COLUMN question_type questiontype NOT NULL DEFAULT 'technical';
                    RAISE NOTICE 'Added column: questions.question_type';
                ELSE
                    RAISE NOTICE 'Column questions.question_type already exists';
                END IF;
            END $$;
            """
            await conn.execute(text(fix_sql))
            print("✓ Successfully checked/added question_type column to questions table!")
    except Exception as e:
        print(f"✗ Error fixing questions schema: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        await engine.dispose()

if __name__ == "__main__":
    asyncio.run(fix_question_type_column())
