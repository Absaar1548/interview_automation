"""
Fix Alembic revision issue by updating the alembic_version table.
This script checks the current revision and updates it to a valid one if needed.
"""
import asyncio
import sys
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine
from app.core.config import settings

async def fix_alembic_revision():
    engine = create_async_engine(settings.DATABASE_URL, echo=False)
    try:
        async with engine.begin() as conn:
            # Check current revision
            result = await conn.execute(text("SELECT version_num FROM alembic_version"))
            row = result.fetchone()
            current_revision = row[0] if row else None
            
            print(f"Current revision in database: {current_revision}")
            
            # If the revision is 'fix_missing_columns' or invalid, update it
            # We'll set it to the baseline revision
            if current_revision == 'fix_missing_columns' or current_revision is None:
                # Set to baseline revision
                baseline_revision = '66ed4b635ed8'
                if current_revision is None:
                    # Insert if table is empty
                    await conn.execute(
                        text("INSERT INTO alembic_version (version_num) VALUES (:revision)"),
                        {"revision": baseline_revision}
                    )
                    print(f"✓ Inserted baseline revision: {baseline_revision}")
                else:
                    # Update existing revision
                    await conn.execute(
                        text("UPDATE alembic_version SET version_num = :revision"),
                        {"revision": baseline_revision}
                    )
                    print(f"✓ Updated alembic_version from '{current_revision}' to baseline revision: {baseline_revision}")
            else:
                print(f"✓ Current revision '{current_revision}' is valid. No changes needed.")
                
    except Exception as e:
        print(f"✗ Error fixing alembic revision: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        await engine.dispose()

if __name__ == "__main__":
    asyncio.run(fix_alembic_revision())
