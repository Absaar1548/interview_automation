"""
Fix Alembic migration state by checking what columns/tables exist
and updating the alembic_version to the correct revision.
"""
import asyncio
import sys
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine
from app.core.config import settings

async def fix_migration_state():
    engine = create_async_engine(settings.DATABASE_URL, echo=False)
    try:
        async with engine.begin() as conn:
            # Check current revision
            result = await conn.execute(text("SELECT version_num FROM alembic_version"))
            row = result.fetchone()
            current_revision = row[0] if row else None
            
            print(f"Current revision in database: {current_revision}")
            
            # Check what columns/tables exist
            # Check if question_type column exists
            result = await conn.execute(text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'questions' AND column_name = 'question_type'
            """))
            question_type_exists = result.fetchone() is not None
            
            # Check if config columns exist
            result = await conn.execute(text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'interview_templates' AND column_name = 'technical_config'
            """))
            technical_config_exists = result.fetchone() is not None
            
            # Determine the correct revision based on what exists
            if question_type_exists and technical_config_exists:
                # Both exist, set to ebfb639c6ea6 (after both migrations)
                target_revision = 'ebfb639c6ea6'
                print(f"Both question_type and config columns exist. Setting revision to: {target_revision}")
            elif question_type_exists:
                # Only question_type exists, set to b8f4adf72de3 (after question_type migration)
                target_revision = 'b8f4adf72de3'
                print(f"Only question_type exists. Setting revision to: {target_revision}")
            else:
                # Nothing exists, keep at baseline
                target_revision = '66ed4b635ed8'
                print(f"Columns don't exist. Keeping at baseline: {target_revision}")
            
            # Update revision if needed
            if current_revision != target_revision:
                await conn.execute(
                    text("UPDATE alembic_version SET version_num = :revision"),
                    {"revision": target_revision}
                )
                print(f"✓ Updated alembic_version from '{current_revision}' to '{target_revision}'")
            else:
                print(f"✓ Current revision '{current_revision}' is correct. No changes needed.")
                
    except Exception as e:
        print(f"✗ Error fixing migration state: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        await engine.dispose()

if __name__ == "__main__":
    asyncio.run(fix_migration_state())
