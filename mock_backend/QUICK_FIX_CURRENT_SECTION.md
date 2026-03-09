# Quick Fix: Add current_section_id Column

The `current_section_id` column is missing from the `interview_sessions` table.

## Option 1: Run the Migration (Recommended)
```bash
cd mock_backend
alembic upgrade head
```

## Option 2: Run SQL Script Directly
Connect to your PostgreSQL database and run:
```sql
-- Add current_section_id column to interview_sessions table if it doesn't exist
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'interview_sessions' AND column_name = 'current_section_id'
    ) THEN
        -- Check if interview_session_sections table exists
        IF EXISTS (
            SELECT 1 FROM information_schema.tables 
            WHERE table_name = 'interview_session_sections'
        ) THEN
            ALTER TABLE interview_sessions 
            ADD COLUMN current_section_id UUID 
            REFERENCES interview_session_sections(id) ON DELETE SET NULL;
            RAISE NOTICE 'Added column: interview_sessions.current_section_id with foreign key';
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
```

## Option 3: Run Python Script
```bash
cd mock_backend
python fix_current_section_id.py
```

After running any of these options, restart your backend server.
