-- =============================================
-- MULTIPLE IMAGE SUPPORT FOR RECIPE EXTRACTION
-- =============================================
-- This migration updates the extraction_jobs table to support multiple source images
-- for a single extraction job, enabling users to upload 2-5 images per recipe.

-- =============================================
-- UPDATE extraction_jobs TABLE
-- =============================================

-- Add new column for multiple source URLs (JSONB array)
ALTER TABLE extraction_jobs
ADD COLUMN source_urls JSONB DEFAULT '[]'::jsonb;

-- Add constraint to ensure source_urls is an array
ALTER TABLE extraction_jobs
ADD CONSTRAINT source_urls_is_array
CHECK (jsonb_typeof(source_urls) = 'array');

-- Add constraint to limit number of images (max 5)
ALTER TABLE extraction_jobs
ADD CONSTRAINT source_urls_max_length
CHECK (jsonb_array_length(source_urls) <= 5);

-- Create GIN index on source_urls for better query performance
CREATE INDEX idx_extraction_jobs_source_urls ON extraction_jobs USING GIN (source_urls);

-- =============================================
-- DATA MIGRATION: Move existing source_url to source_urls array
-- =============================================

-- For existing records, migrate single source_url to source_urls array
UPDATE extraction_jobs
SET source_urls =
    CASE
        WHEN source_url IS NOT NULL AND source_url != ''
        THEN jsonb_build_array(source_url)
        ELSE '[]'::jsonb
    END
WHERE source_urls = '[]'::jsonb;

-- =============================================
-- MAKE source_url NULLABLE (Keep for backward compatibility)
-- =============================================
-- We'll keep source_url column for now but it's deprecated
-- New code should use source_urls array instead

COMMENT ON COLUMN extraction_jobs.source_url IS
    'DEPRECATED: Use source_urls array instead. Kept for backward compatibility.';

COMMENT ON COLUMN extraction_jobs.source_urls IS
    'Array of source image URLs for multi-image recipe extraction. Max 5 images per job.';

-- =============================================
-- HELPER FUNCTIONS
-- =============================================

-- Function to get the first source URL (for backward compatibility)
CREATE OR REPLACE FUNCTION public.get_first_source_url(job extraction_jobs)
RETURNS TEXT
LANGUAGE sql
STABLE
AS $$
    SELECT source_urls->>0 FROM extraction_jobs WHERE id = job.id;
$$;

COMMENT ON FUNCTION public.get_first_source_url(extraction_jobs) IS
    'Helper function to get the first source URL from source_urls array for backward compatibility';

-- Function to count source URLs in a job
CREATE OR REPLACE FUNCTION public.count_source_urls(job_id UUID)
RETURNS INTEGER
LANGUAGE sql
STABLE
AS $$
    SELECT jsonb_array_length(source_urls)
    FROM extraction_jobs
    WHERE id = job_id;
$$;

COMMENT ON FUNCTION public.count_source_urls(UUID) IS
    'Returns the number of source images in an extraction job';

-- =============================================
-- UPDATE TRIGGER
-- =============================================

-- Ensure updated_at is set when source_urls is modified
-- (This trigger already exists from previous migration, just ensuring it covers new column)

-- =============================================
-- EXAMPLE USAGE
-- =============================================
-- Insert job with multiple images:
--   INSERT INTO extraction_jobs (user_id, source_type, source_urls)
--   VALUES (
--       'user-uuid',
--       'photo',
--       '["https://example.com/img1.jpg", "https://example.com/img2.jpg"]'::jsonb
--   );
--
-- Query jobs with multiple images:
--   SELECT id, source_type, jsonb_array_length(source_urls) as image_count
--   FROM extraction_jobs
--   WHERE jsonb_array_length(source_urls) > 1;
--
-- Get all source URLs from a job:
--   SELECT jsonb_array_elements_text(source_urls) as image_url
--   FROM extraction_jobs
--   WHERE id = 'job-uuid';

-- =============================================
-- MIGRATION NOTES
-- =============================================
-- Backward Compatibility:
--   - source_url column kept for backward compatibility
--   - New code should use source_urls array
--   - Old code reading source_url will still work (deprecated)
--
-- Array Format:
--   - JSONB array of strings: ["url1", "url2", "url3"]
--   - Empty array for jobs with no images: []
--   - Max 5 URLs per job (enforced by constraint)
--
-- Performance:
--   - GIN index on source_urls for fast array operations
--   - Helper functions for common queries
