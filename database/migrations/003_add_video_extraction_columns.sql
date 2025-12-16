-- Migration: 003_add_video_extraction_columns
-- Description: Add columns for client-side video download flow (Instagram workaround)
-- This enables the hybrid extraction flow where the server extracts video URLs
-- and the mobile client downloads videos using the user's IP to bypass Instagram blocking.

-- Expand status column to accommodate 'needs_client_download' (21 chars)
-- Previously varchar(20), now varchar(30) for future flexibility
ALTER TABLE public.extraction_jobs
ALTER COLUMN status TYPE VARCHAR(30);

-- Drop existing check constraint and recreate with new status value
ALTER TABLE public.extraction_jobs DROP CONSTRAINT IF EXISTS extraction_jobs_status_check;
ALTER TABLE public.extraction_jobs ADD CONSTRAINT extraction_jobs_status_check
CHECK (status IN ('pending', 'processing', 'completed', 'failed', 'cancelled', 'duplicate', 'not_a_recipe', 'website_blocked', 'needs_client_download'));

-- Add columns to extraction_jobs table for storing video download info
ALTER TABLE public.extraction_jobs
ADD COLUMN IF NOT EXISTS video_download_url TEXT;

ALTER TABLE public.extraction_jobs
ADD COLUMN IF NOT EXISTS video_metadata JSONB;

ALTER TABLE public.extraction_jobs
ADD COLUMN IF NOT EXISTS temp_video_path TEXT;

-- Add index for finding jobs with temp videos (for cleanup queries)
CREATE INDEX IF NOT EXISTS idx_extraction_jobs_temp_video_path
ON public.extraction_jobs(temp_video_path)
WHERE temp_video_path IS NOT NULL;

-- Add column comments
COMMENT ON COLUMN public.extraction_jobs.video_download_url IS 'Direct MP4 URL for client-side download (Instagram)';
COMMENT ON COLUMN public.extraction_jobs.video_metadata IS 'Metadata extracted from video URL (thumbnail, description, platform)';
COMMENT ON COLUMN public.extraction_jobs.temp_video_path IS 'Path in temp-videos bucket, used for cleanup tracking';

-- Note: pg_cron is not enabled on this Supabase instance.
-- Cleanup of temp videos is handled by:
-- 1. Immediate cleanup in ExtractionService.resume_video_extraction() after processing
-- 2. Supabase bucket lifecycle policy (set expiration on temp-videos bucket)
--
-- If you enable pg_cron in the future, you can schedule cleanup with:
-- SELECT cron.schedule(
--     'cleanup-temp-videos',
--     '0 3 * * *',
--     $$
--     UPDATE public.extraction_jobs
--     SET temp_video_path = NULL
--     WHERE temp_video_path IS NOT NULL
--     AND status IN ('completed', 'failed', 'cancelled')
--     AND updated_at < NOW() - INTERVAL '24 hours';
--     $$
-- );
