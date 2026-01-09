-- Migration: Fix website recipes filter to exclude video platform URLs
-- Description: Add URL-based filtering to catch TikTok/YouTube/Instagram recipes
-- that are missing video_sources records
--
-- Problem: TikTok recipes can slip through the website filter because:
-- 1. They have source_type='link' (from LinkExtractor auto-detection)
-- 2. They may be missing video_sources records (background task failure)
-- 3. The filter relies on NOT EXISTS(video_sources) which doesn't catch these

CREATE OR REPLACE FUNCTION public.get_most_extracted_website_recipes(
    limit_param integer DEFAULT 8,
    offset_param integer DEFAULT 0
)
RETURNS TABLE(recipe_id uuid, extraction_count bigint, unique_extractors bigint)
LANGUAGE plpgsql SECURITY DEFINER
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
      -- Exclude recipes with video_sources records
      AND NOT EXISTS (SELECT 1 FROM video_sources vs WHERE vs.recipe_id = r.id)
      -- Also exclude video platform URLs (safety net for missing video_sources)
      AND (r.source_url IS NULL OR NOT (
          r.source_url ILIKE '%tiktok.com%' OR
          r.source_url ILIKE '%vm.tiktok.com%' OR
          r.source_url ILIKE '%youtube.com%' OR
          r.source_url ILIKE '%youtu.be%' OR
          r.source_url ILIKE '%instagram.com%' OR
          r.source_url ILIKE '%facebook.com/reel%' OR
          r.source_url ILIKE '%facebook.com/watch%'
      ))
    GROUP BY r.id
    HAVING COUNT(DISTINCT urd.user_id) >= 1
    ORDER BY extraction_count DESC
    LIMIT limit_param
    OFFSET offset_param;
END;
$$;

-- Update comment
COMMENT ON FUNCTION public.get_most_extracted_website_recipes(integer, integer) IS
'Returns website-sourced recipes (not from video platforms) ordered by extraction count.
Used for "Popular Recipes Online" discovery section.
Excludes video platform URLs (TikTok, YouTube, Instagram, Facebook) as a safety net.';
