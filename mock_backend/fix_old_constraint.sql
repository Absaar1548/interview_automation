-- Drop old constraint that conflicts with new constraint
ALTER TABLE interview_session_questions 
DROP CONSTRAINT IF EXISTS check_question_or_custom_text;

-- Ensure new constraint exists (will fail if already exists, that's ok)
DO $$ 
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.table_constraints 
        WHERE table_name = 'interview_session_questions' 
        AND constraint_name = 'check_question_payload'
    ) THEN
        ALTER TABLE interview_session_questions 
        ADD CONSTRAINT check_question_payload 
            CHECK (
                (question_type = 'technical' AND question_id IS NOT NULL) OR 
                (question_type = 'coding' AND coding_problem_id IS NOT NULL) OR 
                (question_type = 'conversational' AND conversation_round IS NOT NULL) OR 
                (custom_text IS NOT NULL)
            );
    END IF;
END $$;

-- Ensure question_type constraint exists
DO $$ 
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.table_constraints 
        WHERE table_name = 'interview_session_questions' 
        AND constraint_name = 'check_session_question_type'
    ) THEN
        ALTER TABLE interview_session_questions 
        ADD CONSTRAINT check_session_question_type 
            CHECK (question_type IN ('technical', 'coding', 'conversational'));
    END IF;
END $$;
