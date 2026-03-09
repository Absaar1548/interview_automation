-- Quick fix: Add missing config columns to interview_templates table
-- Run this directly in PostgreSQL if migrations haven't been applied

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
