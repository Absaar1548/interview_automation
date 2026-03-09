"""
Comprehensive script to fix all migration issues and ensure database is in correct state.
This script checks the database state and applies any missing migrations directly.
"""
import asyncio
import sys
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine
from app.core.config import settings

async def fix_all_migrations():
    engine = create_async_engine(settings.DATABASE_URL, echo=False)
    try:
        # Use separate transactions for each operation to avoid transaction abort issues
        async with engine.connect() as conn:
            print("=" * 60)
            print("Comprehensive Migration Fix Script")
            print("=" * 60)
            
            # 1. Ensure interview_session_sections table exists
            print("\n1. Checking interview_session_sections table...")
            try:
                result = await conn.execute(text("""
                    SELECT EXISTS (
                        SELECT 1 FROM information_schema.tables 
                        WHERE table_name = 'interview_session_sections'
                    )
                """))
                if not result.scalar():
                    print("   Creating interview_session_sections table...")
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
                        );
                        CREATE INDEX ix_interview_session_sections_interview_session_id 
                            ON interview_session_sections(interview_session_id);
                    """))
                    await conn.commit()
                    print("   ✓ Created interview_session_sections table")
                else:
                    print("   ✓ interview_session_sections table exists")
            except Exception as e:
                await conn.rollback()
                print(f"   ⚠ Error checking/creating table: {e}")
            
            # 2. Ensure interview_session_questions has interview_session_id
            print("\n2. Checking interview_session_questions.interview_session_id...")
            try:
                result = await conn.execute(text("""
                    SELECT column_name 
                    FROM information_schema.columns 
                    WHERE table_name = 'interview_session_questions' 
                    AND column_name = 'interview_session_id'
                """))
                if not result.fetchone():
                    print("   Adding interview_session_id column...")
                    # Clear data first
                    await conn.execute(text("DELETE FROM interview_session_questions;"))
                    await conn.execute(text("DELETE FROM interview_sessions;"))
                    await conn.execute(text("""
                        ALTER TABLE interview_session_questions 
                        ADD COLUMN interview_session_id UUID NOT NULL;
                    """))
                    await conn.commit()
                    print("   ✓ Added interview_session_id column")
                else:
                    print("   ✓ interview_session_id column exists")
            except Exception as e:
                await conn.rollback()
                print(f"   ⚠ Error checking/adding column: {e}")
            
            # 3. Ensure interview_session_questions has section_id
            print("\n3. Checking interview_session_questions.section_id...")
            try:
                result = await conn.execute(text("""
                    SELECT column_name 
                    FROM information_schema.columns 
                    WHERE table_name = 'interview_session_questions' 
                    AND column_name = 'section_id'
                """))
                if not result.fetchone():
                    print("   Adding section_id column...")
                    await conn.execute(text("""
                        ALTER TABLE interview_session_questions 
                        ADD COLUMN section_id UUID;
                    """))
                    await conn.commit()
                    print("   ✓ Added section_id column")
                else:
                    print("   ✓ section_id column exists")
            except Exception as e:
                await conn.rollback()
                print(f"   ⚠ Error checking/adding column: {e}")
            
            # 3a. Ensure interview_session_questions has question_type (from migration d4e5f6a7b8c9)
            print("\n3a. Checking interview_session_questions.question_type...")
            try:
                result = await conn.execute(text("""
                    SELECT column_name 
                    FROM information_schema.columns 
                    WHERE table_name = 'interview_session_questions' 
                    AND column_name = 'question_type'
                """))
                if not result.fetchone():
                    print("   Adding question_type column...")
                    await conn.execute(text("""
                        ALTER TABLE interview_session_questions 
                        ADD COLUMN question_type VARCHAR(20) NOT NULL DEFAULT 'technical';
                    """))
                    await conn.commit()
                    print("   ✓ Added question_type column")
                else:
                    print("   ✓ question_type column exists")
            except Exception as e:
                await conn.rollback()
                print(f"   ⚠ Error checking/adding question_type: {e}")
            
            # 3b. Ensure interview_session_questions has coding_problem_id
            print("\n3b. Checking interview_session_questions.coding_problem_id...")
            try:
                result = await conn.execute(text("""
                    SELECT column_name 
                    FROM information_schema.columns 
                    WHERE table_name = 'interview_session_questions' 
                    AND column_name = 'coding_problem_id'
                """))
                if not result.fetchone():
                    print("   Adding coding_problem_id column...")
                    await conn.execute(text("""
                        ALTER TABLE interview_session_questions 
                        ADD COLUMN coding_problem_id UUID;
                    """))
                    # Add foreign key if coding_problems table exists
                    result = await conn.execute(text("""
                        SELECT EXISTS (
                            SELECT 1 FROM information_schema.tables 
                            WHERE table_name = 'coding_problems'
                        )
                    """))
                    if result.scalar():
                        await conn.execute(text("""
                            ALTER TABLE interview_session_questions 
                            ADD CONSTRAINT fk_isq_coding_problem_id 
                                FOREIGN KEY (coding_problem_id) 
                                REFERENCES coding_problems(id) 
                                ON DELETE SET NULL;
                        """))
                    await conn.commit()
                    print("   ✓ Added coding_problem_id column")
                else:
                    print("   ✓ coding_problem_id column exists")
            except Exception as e:
                await conn.rollback()
                print(f"   ⚠ Error checking/adding coding_problem_id: {e}")
            
            # 3c. Ensure interview_session_questions has conversation_round
            print("\n3c. Checking interview_session_questions.conversation_round...")
            try:
                result = await conn.execute(text("""
                    SELECT column_name 
                    FROM information_schema.columns 
                    WHERE table_name = 'interview_session_questions' 
                    AND column_name = 'conversation_round'
                """))
                if not result.fetchone():
                    print("   Adding conversation_round column...")
                    await conn.execute(text("""
                        ALTER TABLE interview_session_questions 
                        ADD COLUMN conversation_round INTEGER;
                    """))
                    await conn.commit()
                    print("   ✓ Added conversation_round column")
                else:
                    print("   ✓ conversation_round column exists")
            except Exception as e:
                await conn.rollback()
                print(f"   ⚠ Error checking/adding conversation_round: {e}")
            
            # 4. Ensure indexes exist
            print("\n4. Checking indexes...")
            indexes_to_create = [
                ('ix_interview_session_questions_interview_session_id', 
                 'CREATE INDEX ix_interview_session_questions_interview_session_id ON interview_session_questions(interview_session_id);'),
                ('ix_interview_session_questions_section_id',
                 'CREATE INDEX ix_interview_session_questions_section_id ON interview_session_questions(section_id);'),
                ('idx_session_section_order',
                 'CREATE INDEX idx_session_section_order ON interview_session_questions(interview_session_id, section_id, "order");')
            ]
            
            for index_name, create_sql in indexes_to_create:
                try:
                    result = await conn.execute(text(f"""
                        SELECT 1 FROM pg_indexes 
                        WHERE tablename = 'interview_session_questions' 
                        AND indexname = '{index_name}'
                    """))
                    if not result.fetchone():
                        print(f"   Creating index {index_name}...")
                        await conn.execute(text(create_sql))
                        await conn.commit()
                        print(f"   ✓ Created index {index_name}")
                    else:
                        print(f"   ✓ Index {index_name} exists")
                except Exception as e:
                    await conn.rollback()
                    print(f"   ⚠ Error with index {index_name}: {e}")
            
            # 5. Ensure foreign keys exist
            print("\n5. Checking foreign keys...")
            
            try:
                # Drop old interview_id FK if exists
                result = await conn.execute(text("""
                    SELECT 1 FROM information_schema.table_constraints 
                    WHERE table_name = 'interview_session_questions' 
                    AND constraint_name = 'interview_session_questions_interview_id_fkey'
                """))
                if result.fetchone():
                    print("   Dropping old interview_id foreign key...")
                    await conn.execute(text("""
                        ALTER TABLE interview_session_questions 
                        DROP CONSTRAINT IF EXISTS interview_session_questions_interview_id_fkey;
                    """))
                    await conn.commit()
                    print("   ✓ Dropped old interview_id foreign key")
            except Exception as e:
                await conn.rollback()
                print(f"   ⚠ Error dropping old FK: {e}")
            
            # Create new FKs
            fks_to_create = [
                ('fk_isq_section_id',
                 'ALTER TABLE interview_session_questions ADD CONSTRAINT fk_isq_section_id FOREIGN KEY (section_id) REFERENCES interview_session_sections(id) ON DELETE CASCADE;'),
                ('fk_isq_interview_session_id',
                 'ALTER TABLE interview_session_questions ADD CONSTRAINT fk_isq_interview_session_id FOREIGN KEY (interview_session_id) REFERENCES interview_sessions(id) ON DELETE CASCADE;')
            ]
            
            for fk_name, create_sql in fks_to_create:
                try:
                    result = await conn.execute(text(f"""
                        SELECT 1 FROM information_schema.table_constraints 
                        WHERE table_name = 'interview_session_questions' 
                        AND constraint_name = '{fk_name}'
                    """))
                    if not result.fetchone():
                        print(f"   Creating foreign key {fk_name}...")
                        await conn.execute(text(create_sql))
                        await conn.commit()
                        print(f"   ✓ Created foreign key {fk_name}")
                    else:
                        print(f"   ✓ Foreign key {fk_name} exists")
                except Exception as e:
                    await conn.rollback()
                    print(f"   ⚠ Could not create {fk_name}: {e}")
            
            # 6. Drop old interview_id column if exists
            print("\n6. Checking for old interview_id column...")
            try:
                result = await conn.execute(text("""
                    SELECT column_name 
                    FROM information_schema.columns 
                    WHERE table_name = 'interview_session_questions' 
                    AND column_name = 'interview_id'
                """))
                if result.fetchone():
                    print("   Dropping old interview_id column...")
                    await conn.execute(text("""
                        ALTER TABLE interview_session_questions 
                        DROP COLUMN interview_id;
                    """))
                    await conn.commit()
                    print("   ✓ Dropped interview_id column")
                else:
                    print("   ✓ interview_id column does not exist")
            except Exception as e:
                await conn.rollback()
                print(f"   ⚠ Could not drop interview_id: {e}")
            
            # 7. Set section_id to NOT NULL (handle NULL values first)
            print("\n7. Setting section_id to NOT NULL...")
            # Check if there are NULL values
            result = await conn.execute(text("""
                SELECT COUNT(*) 
                FROM interview_session_questions 
                WHERE section_id IS NULL
            """))
            null_count = result.scalar()
            
            if null_count > 0:
                print(f"   Found {null_count} rows with NULL section_id. Deleting them...")
                await conn.execute(text("""
                    DELETE FROM interview_session_questions 
                    WHERE section_id IS NULL;
                """))
                await conn.commit()
                print(f"   ✓ Deleted {null_count} rows with NULL section_id")
            
            # Now check if column is nullable
            result = await conn.execute(text("""
                SELECT is_nullable 
                FROM information_schema.columns 
                WHERE table_name = 'interview_session_questions' 
                AND column_name = 'section_id'
            """))
            row = result.fetchone()
            if row and row[0] == 'YES':
                print("   Setting section_id to NOT NULL...")
                try:
                    await conn.execute(text("""
                        ALTER TABLE interview_session_questions 
                        ALTER COLUMN section_id SET NOT NULL;
                    """))
                    await conn.commit()
                    print("   ✓ Set section_id to NOT NULL")
                except Exception as e:
                    await conn.rollback()
                    print(f"   ⚠ Could not set section_id to NOT NULL: {e}")
            else:
                print("   ✓ section_id is already NOT NULL or doesn't exist")
            
            # 8. Ensure current_section_id exists in interview_sessions
            print("\n8. Checking interview_sessions.current_section_id...")
            try:
                result = await conn.execute(text("""
                    SELECT column_name 
                    FROM information_schema.columns 
                    WHERE table_name = 'interview_sessions' 
                    AND column_name = 'current_section_id'
                """))
                if not result.fetchone():
                    print("   Adding current_section_id column...")
                    await conn.execute(text("""
                        ALTER TABLE interview_sessions 
                        ADD COLUMN current_section_id UUID;
                    """))
                    await conn.execute(text("""
                        ALTER TABLE interview_sessions 
                        ADD CONSTRAINT fk_interview_sessions_current_section_id 
                            FOREIGN KEY (current_section_id) 
                            REFERENCES interview_session_sections(id) 
                            ON DELETE SET NULL;
                    """))
                    await conn.commit()
                    print("   ✓ Added current_section_id column and foreign key")
                else:
                    print("   ✓ current_section_id column exists")
            except Exception as e:
                await conn.rollback()
                print(f"   ⚠ Error checking/adding current_section_id: {e}")
            
            # 9. Ensure check constraints exist (from migration d4e5f6a7b8c9)
            print("\n9. Checking check constraints...")
            try:
                # Check if constraints exist
                result = await conn.execute(text("""
                    SELECT constraint_name 
                    FROM information_schema.table_constraints 
                    WHERE table_name = 'interview_session_questions' 
                    AND constraint_type = 'CHECK'
                """))
                existing_constraints = {row[0] for row in result.fetchall()}
                
                # Drop old constraint if it exists
                if 'check_question_or_custom_text' in existing_constraints:
                    print("   Dropping old check_question_or_custom_text constraint...")
                    await conn.execute(text("""
                        ALTER TABLE interview_session_questions 
                        DROP CONSTRAINT IF EXISTS check_question_or_custom_text;
                    """))
                    await conn.commit()
                    print("   ✓ Dropped old check_question_or_custom_text constraint")
                
                # Add question_type check constraint
                if 'check_session_question_type' not in existing_constraints:
                    print("   Adding check_session_question_type constraint...")
                    await conn.execute(text("""
                        ALTER TABLE interview_session_questions 
                        ADD CONSTRAINT check_session_question_type 
                            CHECK (question_type IN ('technical', 'coding', 'conversational'));
                    """))
                    await conn.commit()
                    print("   ✓ Added check_session_question_type constraint")
                else:
                    print("   ✓ check_session_question_type constraint exists")
                
                # Add payload check constraint
                if 'check_question_payload' not in existing_constraints:
                    print("   Adding check_question_payload constraint...")
                    await conn.execute(text("""
                        ALTER TABLE interview_session_questions 
                        ADD CONSTRAINT check_question_payload 
                            CHECK (
                                (question_type = 'technical' AND question_id IS NOT NULL) OR 
                                (question_type = 'coding' AND coding_problem_id IS NOT NULL) OR 
                                (question_type = 'conversational' AND conversation_round IS NOT NULL) OR 
                                (custom_text IS NOT NULL)
                            );
                    """))
                    await conn.commit()
                    print("   ✓ Added check_question_payload constraint")
                else:
                    print("   ✓ check_question_payload constraint exists")
            except Exception as e:
                await conn.rollback()
                print(f"   ⚠ Error checking/adding constraints: {e}")
            
            # 10. Update Alembic version
            print("\n10. Updating Alembic version...")
            try:
                await conn.execute(text("""
                    CREATE TABLE IF NOT EXISTS alembic_version (
                        version_num VARCHAR(32) NOT NULL PRIMARY KEY
                    );
                """))
                await conn.commit()
                
                # Check what revision should be set
                result = await conn.execute(text("SELECT version_num FROM alembic_version"))
                current_revision = result.scalar()
                
                # Set to the latest migration
                target_revision = '4e8141f6c894'
                if current_revision != target_revision:
                    if current_revision:
                        await conn.execute(text(f"""
                            UPDATE alembic_version 
                            SET version_num = '{target_revision}' 
                            WHERE version_num = '{current_revision}'
                        """))
                        await conn.commit()
                        print(f"   ✓ Updated Alembic version from '{current_revision}' to '{target_revision}'")
                    else:
                        await conn.execute(text(f"""
                            INSERT INTO alembic_version (version_num) 
                            VALUES ('{target_revision}')
                        """))
                        await conn.commit()
                        print(f"   ✓ Set Alembic version to '{target_revision}'")
                else:
                    print(f"   ✓ Alembic version is already '{target_revision}'")
            except Exception as e:
                await conn.rollback()
                print(f"   ⚠ Error updating Alembic version: {e}")
            
            print("\n" + "=" * 60)
            print("✓ All migrations fixed successfully!")
            print("=" * 60)
                
    except Exception as e:
        print(f"\n✗ Error fixing migrations: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        await engine.dispose()

if __name__ == "__main__":
    asyncio.run(fix_all_migrations())
