"""
Quick fix script to add missing config columns to interview_templates table.
Run this if you get: column "technical_config" of relation "interview_templates" does not exist
"""

import asyncio
import sys
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine
from app.core.config import settings

async def add_template_config_columns():
    engine = create_async_engine(settings.DATABASE_URL, echo=False)
    try:
        async with engine.begin() as conn:
            print("Checking and adding missing config columns to interview_templates...")
            fix_sql = """
            DO $$
            BEGIN
                -- Add technical_config if it doesn't exist
                IF NOT EXISTS (
                    SELECT 1 FROM information_schema.columns 
                    WHERE table_name = 'interview_templates' AND column_name = 'technical_config'
                ) THEN
                    ALTER TABLE interview_templates ADD COLUMN technical_config JSONB;
                    RAISE NOTICE 'Added column: interview_templates.technical_config';
                END IF;
                
                -- Add coding_config if it doesn't exist
                IF NOT EXISTS (
                    SELECT 1 FROM information_schema.columns 
                    WHERE table_name = 'interview_templates' AND column_name = 'coding_config'
                ) THEN
                    ALTER TABLE interview_templates ADD COLUMN coding_config JSONB;
                    RAISE NOTICE 'Added column: interview_templates.coding_config';
                END IF;
                
                -- Add conversational_config if it doesn't exist
                IF NOT EXISTS (
                    SELECT 1 FROM information_schema.columns 
                    WHERE table_name = 'interview_templates' AND column_name = 'conversational_config'
                ) THEN
                    ALTER TABLE interview_templates ADD COLUMN conversational_config JSONB;
                    RAISE NOTICE 'Added column: interview_templates.conversational_config';
                END IF;
            END $$;
            """
            await conn.execute(text(fix_sql))
            print("✓ Successfully added missing config columns to interview_templates!")
    except Exception as e:
        print(f"✗ Error fixing interview_templates schema: {e}")
        sys.exit(1)
    finally:
        await engine.dispose()

if __name__ == "__main__":
    asyncio.run(add_template_config_columns())
