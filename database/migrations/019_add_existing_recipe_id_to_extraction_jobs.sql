-- Add existing_recipe_id column to extraction_jobs for duplicate detection
-- This stores the ID of an already-extracted recipe when a duplicate video is detected

ALTER TABLE extraction_jobs
ADD COLUMN existing_recipe_id UUID REFERENCES recipes(id) ON DELETE SET NULL;

-- Add comment explaining the column
COMMENT ON COLUMN extraction_jobs.existing_recipe_id IS 'References an existing recipe when duplicate video is detected during extraction';
