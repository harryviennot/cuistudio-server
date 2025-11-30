-- Migration: Add 'link' source type and remove 'url' source type
-- Created: 2025-11-30
-- Description: Adds 'link' as a valid source_type and removes 'url' for both extraction_jobs and recipes tables.
--              The LINK type auto-detects whether a URL is a video platform (TikTok, YouTube, Instagram)
--              or a regular recipe webpage, and routes to the appropriate extraction method.
--              URL source type is removed as it's replaced by LINK.

-- ============================================================================
-- UPDATE EXTRACTION_JOBS SOURCE_TYPE CONSTRAINT
-- ============================================================================

-- Drop the existing check constraint
ALTER TABLE extraction_jobs
DROP CONSTRAINT IF EXISTS extraction_jobs_source_type_check;

-- Add the updated check constraint with 'link' included and 'url' removed
ALTER TABLE extraction_jobs
ADD CONSTRAINT extraction_jobs_source_type_check
CHECK (source_type IN ('video', 'photo', 'voice', 'paste', 'link'));

-- ============================================================================
-- UPDATE RECIPES SOURCE_TYPE CONSTRAINT
-- ============================================================================

-- Drop the existing check constraint
ALTER TABLE recipes
DROP CONSTRAINT IF EXISTS recipes_source_type_check;

-- Add the updated check constraint with 'link' included and 'url' removed
ALTER TABLE recipes
ADD CONSTRAINT recipes_source_type_check
CHECK (source_type IN ('video', 'photo', 'voice', 'paste', 'link'));

-- ============================================================================
-- VERIFICATION
-- ============================================================================

DO $$
BEGIN
    -- Verify extraction_jobs constraint exists
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.constraint_column_usage
        WHERE constraint_name = 'extraction_jobs_source_type_check'
        AND table_name = 'extraction_jobs'
    ) THEN
        RAISE EXCEPTION 'Migration failed: extraction_jobs_source_type_check constraint not found';
    END IF;

    -- Verify recipes constraint exists
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.constraint_column_usage
        WHERE constraint_name = 'recipes_source_type_check'
        AND table_name = 'recipes'
    ) THEN
        RAISE EXCEPTION 'Migration failed: recipes_source_type_check constraint not found';
    END IF;

    RAISE NOTICE 'Migration successful: link source type added to extraction_jobs and recipes tables';
END $$;
