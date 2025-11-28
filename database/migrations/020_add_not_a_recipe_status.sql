-- =============================================
-- ADD NOT_A_RECIPE STATUS TO EXTRACTION JOBS
-- =============================================
-- This migration adds the 'not_a_recipe' status to the extraction_jobs table
-- to support detection of non-recipe content during extraction.

-- Drop the existing check constraint
ALTER TABLE extraction_jobs
DROP CONSTRAINT IF EXISTS extraction_jobs_status_check;

-- Add the updated check constraint with the new status value
ALTER TABLE extraction_jobs
ADD CONSTRAINT extraction_jobs_status_check
CHECK (status IN ('pending', 'processing', 'completed', 'failed', 'not_a_recipe'));

-- Add comment explaining the status values
COMMENT ON COLUMN extraction_jobs.status IS
    'Job status: pending (waiting), processing (in progress), completed (success), failed (error), not_a_recipe (content does not contain a recipe)';
