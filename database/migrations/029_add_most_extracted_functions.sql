-- Migration: Add functions for most extracted recipes discovery
-- These functions support the discovery endpoints for "Trending on Socials" and "Popular Recipes Online"

-- Function to get most extracted video recipes (TikTok, Instagram, YouTube)
CREATE OR REPLACE FUNCTION get_most_extracted_video_recipes(
    limit_param INTEGER DEFAULT 8,
    offset_param INTEGER DEFAULT 0
)
RETURNS TABLE (
    recipe_id UUID,
    extraction_count BIGINT,
    unique_extractors BIGINT
)
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
BEGIN
    RETURN QUERY
    SELECT
        r.id as recipe_id,
        COUNT(DISTINCT urd.user_id) as extraction_count,
        COUNT(DISTINCT urd.user_id) as unique_extractors
    FROM recipes r
    INNER JOIN video_sources vs ON vs.recipe_id = r.id
    INNER JOIN user_recipe_data urd ON urd.recipe_id = r.id AND urd.was_extracted = true
    WHERE r.is_public = true AND r.is_draft = false
    GROUP BY r.id
    HAVING COUNT(DISTINCT urd.user_id) >= 1
    ORDER BY extraction_count DESC
    LIMIT limit_param
    OFFSET offset_param;
END;
$$;

COMMENT ON FUNCTION get_most_extracted_video_recipes IS
'Returns video-sourced recipes (TikTok, Instagram, YouTube) ordered by extraction count.
Used for "Trending on Socials" discovery section.';


-- Function to get most extracted website recipes (recipe websites, not videos)
CREATE OR REPLACE FUNCTION get_most_extracted_website_recipes(
    limit_param INTEGER DEFAULT 8,
    offset_param INTEGER DEFAULT 0
)
RETURNS TABLE (
    recipe_id UUID,
    extraction_count BIGINT,
    unique_extractors BIGINT
)
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
BEGIN
    RETURN QUERY
    SELECT
        r.id as recipe_id,
        COUNT(DISTINCT urd.user_id) as extraction_count,
        COUNT(DISTINCT urd.user_id) as unique_extractors
    FROM recipes r
    INNER JOIN user_recipe_data urd ON urd.recipe_id = r.id AND urd.was_extracted = true
    WHERE r.is_public = true
      AND r.is_draft = false
      AND r.source_type = 'link'
      AND NOT EXISTS (
          SELECT 1 FROM video_sources vs WHERE vs.recipe_id = r.id
      )
    GROUP BY r.id
    HAVING COUNT(DISTINCT urd.user_id) >= 1
    ORDER BY extraction_count DESC
    LIMIT limit_param
    OFFSET offset_param;
END;
$$;

COMMENT ON FUNCTION get_most_extracted_website_recipes IS
'Returns website-sourced recipes (not from video platforms) ordered by extraction count.
Used for "Popular Recipes Online" discovery section.';


-- Add indexes to support these queries efficiently
CREATE INDEX IF NOT EXISTS idx_user_recipe_data_was_extracted
ON user_recipe_data(recipe_id, user_id)
WHERE was_extracted = true;

CREATE INDEX IF NOT EXISTS idx_recipes_public_not_draft
ON recipes(id)
WHERE is_public = true AND is_draft = false;


-- Verification
DO $$
BEGIN
    -- Verify functions were created
    IF NOT EXISTS (
        SELECT 1 FROM pg_proc WHERE proname = 'get_most_extracted_video_recipes'
    ) THEN
        RAISE EXCEPTION 'Migration failed: get_most_extracted_video_recipes function not created';
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM pg_proc WHERE proname = 'get_most_extracted_website_recipes'
    ) THEN
        RAISE EXCEPTION 'Migration failed: get_most_extracted_website_recipes function not created';
    END IF;

    RAISE NOTICE 'Migration 029 completed successfully: most extracted functions created';
END;
$$;
