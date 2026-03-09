-- Fix Alembic revision issue
-- If the alembic_version table has 'fix_missing_columns' as the current revision,
-- update it to the baseline revision so migrations can run

-- First, check what's in the table
SELECT version_num FROM alembic_version;

-- If the revision is 'fix_missing_columns', update it to the baseline
-- Uncomment the line below and run it if needed:
-- UPDATE alembic_version SET version_num = '66ed4b635ed8' WHERE version_num = 'fix_missing_columns';

-- Or if the table is empty or has an invalid revision, insert the baseline:
-- DELETE FROM alembic_version;
-- INSERT INTO alembic_version (version_num) VALUES ('66ed4b635ed8');
