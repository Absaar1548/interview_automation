-- Quick fix: Add missing question_type column to questions table
-- Run this directly in PostgreSQL if migrations haven't been applied

DO $$
BEGIN
    -- Create the enum type if it doesn't exist
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'questiontype') THEN
        CREATE TYPE questiontype AS ENUM ('technical', 'behavioral', 'coding');
        RAISE NOTICE 'Created enum type: questiontype';
    END IF;
    
    -- Add question_type column if it doesn't exist
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'questions' AND column_name = 'question_type'
    ) THEN
        ALTER TABLE questions ADD COLUMN question_type questiontype NOT NULL DEFAULT 'technical';
        RAISE NOTICE 'Added column: questions.question_type';
    ELSE
        RAISE NOTICE 'Column questions.question_type already exists';
    END IF;
END $$;
