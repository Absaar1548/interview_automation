"""
Quick fix script to drop the old check_question_or_custom_text constraint
that conflicts with the new check_question_payload constraint.
"""
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text
from app.core.config import settings

async def fix_constraint():
    """Drop the old constraint and ensure the new one exists."""
    engine = create_async_engine(
        settings.DATABASE_URL,
        echo=False,
    )
    
    async with engine.begin() as conn:
        try:
            # Check existing constraints
            result = await conn.execute(text("""
                SELECT constraint_name 
                FROM information_schema.table_constraints 
                WHERE table_name = 'interview_session_questions' 
                AND constraint_type = 'CHECK'
            """))
            existing_constraints = {row[0] for row in result.fetchall()}
            
            print("Existing CHECK constraints:")
            for constraint in existing_constraints:
                print(f"  - {constraint}")
            
            # Drop old constraint if it exists
            if 'check_question_or_custom_text' in existing_constraints:
                print("\nDropping old constraint: check_question_or_custom_text")
                await conn.execute(text("""
                    ALTER TABLE interview_session_questions 
                    DROP CONSTRAINT IF EXISTS check_question_or_custom_text;
                """))
                print("✓ Dropped old constraint")
            else:
                print("\n✓ Old constraint check_question_or_custom_text not found (already removed)")
            
            # Ensure new constraint exists
            if 'check_question_payload' not in existing_constraints:
                print("\nAdding new constraint: check_question_payload")
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
                print("✓ Added new constraint")
            else:
                print("\n✓ New constraint check_question_payload already exists")
            
            # Ensure question_type constraint exists
            if 'check_session_question_type' not in existing_constraints:
                print("\nAdding constraint: check_session_question_type")
                await conn.execute(text("""
                    ALTER TABLE interview_session_questions 
                    ADD CONSTRAINT check_session_question_type 
                        CHECK (question_type IN ('technical', 'coding', 'conversational'));
                """))
                print("✓ Added question_type constraint")
            else:
                print("\n✓ Constraint check_session_question_type already exists")
            
            print("\n✅ All constraints fixed!")
            
        await engine.dispose()
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        raise

if __name__ == "__main__":
    asyncio.run(fix_constraint())
