-- Migration: Add 'website_blocked' to extraction_jobs status constraint
-- Created: 2025-11-30
-- Description: Adds 'website_blocked' as a valid status for extraction_jobs table.
--              This status is used when a website returns 403 Forbidden and blocks
--              automated recipe extraction.

-- ============================================================================
-- UPDATE EXTRACTION_JOBS STATUS CONSTRAINT
-- ============================================================================

-- Drop the existing check constraint
ALTER TABLE extraction_jobs
DROP CONSTRAINT IF EXISTS extraction_jobs_status_check;

-- Add the updated check constraint with 'website_blocked' included
ALTER TABLE extraction_jobs
ADD CONSTRAINT extraction_jobs_status_check
CHECK (status IN ('pending', 'processing', 'completed', 'failed', 'not_a_recipe', 'website_blocked'));

-- ============================================================================
-- VERIFICATION
-- ============================================================================

DO $$
BEGIN
    -- Verify extraction_jobs constraint exists
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.constraint_column_usage
        WHERE constraint_name = 'extraction_jobs_status_check'
        AND table_name = 'extraction_jobs'
    ) THEN
        RAISE EXCEPTION 'Migration failed: extraction_jobs_status_check constraint not found';
    END IF;

    RAISE NOTICE 'Migration successful: website_blocked status added to extraction_jobs table';
END $$;
