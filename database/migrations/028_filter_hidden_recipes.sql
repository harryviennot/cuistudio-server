-- Migration: Filter hidden recipes from public queries
-- Date: 2025-01-19
-- Description: Treat hidden recipes (is_hidden=true) as private
--              - Hidden recipes won't appear in discovery feeds, search, or public listings
--              - Owners can still access their hidden recipes
--              - Affects: trending, popular, highest-rated, most-extracted, search, materialized view

-- ============================================================================
-- 1. UPDATE get_trending_recipes - add is_hidden filter
-- ============================================================================
CREATE OR REPLACE FUNCTION public.get_trending_recipes(
    time_window_days integer DEFAULT 7,
    limit_param integer DEFAULT 20,
    offset_param integer DEFAULT 0
)
RETURNS TABLE(recipe_id uuid, cook_count bigint, unique_users bigint)
LANGUAGE plpgsql STABLE
AS $$
BEGIN
    RETURN QUERY
    SELECT
        rce.recipe_id,
        COUNT(*) as cook_count,
        COUNT(DISTINCT rce.user_id) as unique_users
    FROM recipe_cooking_events rce
    INNER JOIN recipes r ON r.id = rce.recipe_id
    WHERE
        rce.cooked_at >= NOW() - INTERVAL '1 day' * time_window_days
        AND r.is_public = true
        AND r.is_draft = false
        AND r.is_hidden = false  -- NEW: exclude hidden recipes
    GROUP BY rce.recipe_id
    ORDER BY cook_count DESC
    LIMIT limit_param
    OFFSET offset_param;
END;
$$;

COMMENT ON FUNCTION public.get_trending_recipes(integer, integer, integer) IS
'Returns recipes ordered by cooking frequency in the specified time window.
Excludes hidden recipes (moderated content). Includes cook count and unique user count.';

-- ============================================================================
-- 2. UPDATE get_most_extracted_video_recipes - add is_hidden filter
-- ============================================================================
CREATE OR REPLACE FUNCTION public.get_most_extracted_video_recipes(
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
    INNER JOIN video_sources vs ON vs.recipe_id = r.id
    INNER JOIN user_recipe_data urd ON urd.recipe_id = r.id AND urd.was_extracted = true
    WHERE r.is_public = true
      AND r.is_draft = false
      AND r.is_hidden = false  -- NEW: exclude hidden recipes
    GROUP BY r.id
    HAVING COUNT(DISTINCT urd.user_id) >= 1
    ORDER BY extraction_count DESC
    LIMIT limit_param
    OFFSET offset_param;
END;
$$;

COMMENT ON FUNCTION public.get_most_extracted_video_recipes(integer, integer) IS
'Returns video-sourced recipes (TikTok, Instagram, YouTube) ordered by extraction count.
Used for "Trending on Socials" discovery section. Excludes hidden recipes.';

-- ============================================================================
-- 3. UPDATE get_most_extracted_website_recipes - add is_hidden filter
-- ============================================================================
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
      AND r.is_hidden = false  -- NEW: exclude hidden recipes
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

COMMENT ON FUNCTION public.get_most_extracted_website_recipes(integer, integer) IS
'Returns website-sourced recipes (not from video platforms) ordered by extraction count.
Used for "Popular Recipes Online" discovery section. Excludes hidden recipes.';

-- ============================================================================
-- 4. UPDATE search_recipes_full_text - add is_hidden filter (owner can see own)
-- ============================================================================
-- Must drop first because we're recreating with same signature
DROP FUNCTION IF EXISTS public.search_recipes_full_text(text, uuid, integer, integer, text, uuid[], integer, integer, integer, integer, integer);

CREATE FUNCTION public.search_recipes_full_text(
    search_query text,
    user_id_param uuid DEFAULT NULL::uuid,
    limit_param integer DEFAULT 20,
    offset_param integer DEFAULT 0,
    difficulty_param text DEFAULT NULL,
    category_ids_param uuid[] DEFAULT NULL,
    max_prep_time_param integer DEFAULT NULL,
    max_cook_time_param integer DEFAULT NULL,
    max_rest_time_param integer DEFAULT NULL,
    min_total_time_param integer DEFAULT NULL,
    max_total_time_param integer DEFAULT NULL
)
RETURNS TABLE(
    id uuid,
    title character varying,
    description text,
    image_url text,
    servings integer,
    difficulty character varying,
    tags text[],
    category_id uuid,
    prep_time_minutes integer,
    cook_time_minutes integer,
    total_time_minutes integer,
    resting_time_minutes integer,
    created_by uuid,
    is_public boolean,
    fork_count integer,
    average_rating numeric,
    rating_count integer,
    total_times_cooked integer,
    created_at timestamp with time zone,
    source_type character varying,
    rank real
)
LANGUAGE plpgsql STABLE
AS $$
DECLARE
  query_tsquery tsquery;
BEGIN
  -- Pre-compile the tsquery once for better performance
  query_tsquery := plainto_tsquery('simple', search_query);

  RETURN QUERY
  SELECT
    r.id,
    r.title,
    r.description,
    r.image_url,
    r.servings,
    r.difficulty,
    r.tags,
    r.category_id,
    r.prep_time_minutes,
    r.cook_time_minutes,
    r.total_time_minutes,
    r.resting_time_minutes,
    r.created_by,
    r.is_public,
    r.fork_count,
    r.average_rating,
    r.rating_count,
    r.total_times_cooked,
    r.created_at,
    r.source_type,
    ts_rank_cd(r.search_vector, query_tsquery, 32) as rank
  FROM recipes r
  WHERE
    -- Full-text search (uses GIN index)
    r.search_vector @@ query_tsquery
    -- Access control: public recipes OR user's own recipes
    AND (r.is_public = true OR (user_id_param IS NOT NULL AND r.created_by = user_id_param))
    -- Hidden filter: exclude hidden recipes UNLESS it's the owner viewing
    AND (r.is_hidden = false OR (user_id_param IS NOT NULL AND r.created_by = user_id_param))
    -- Optional filters (all use short-circuit evaluation)
    AND (difficulty_param IS NULL OR r.difficulty = difficulty_param)
    AND (category_ids_param IS NULL OR r.category_id = ANY(category_ids_param))
    AND (max_prep_time_param IS NULL OR r.prep_time_minutes IS NULL OR r.prep_time_minutes <= max_prep_time_param)
    AND (max_cook_time_param IS NULL OR r.cook_time_minutes IS NULL OR r.cook_time_minutes <= max_cook_time_param)
    AND (max_rest_time_param IS NULL OR r.resting_time_minutes IS NULL OR r.resting_time_minutes <= max_rest_time_param)
    AND (min_total_time_param IS NULL OR r.total_time_minutes >= min_total_time_param)
    AND (max_total_time_param IS NULL OR r.total_time_minutes IS NULL OR r.total_time_minutes <= max_total_time_param)
  ORDER BY rank DESC, r.created_at DESC
  LIMIT limit_param
  OFFSET offset_param;
END;
$$;

COMMENT ON FUNCTION public.search_recipes_full_text IS
'Optimized full-text search with database-side filtering.
Excludes hidden recipes from results (owners can still see their own hidden recipes).
All filter parameters are optional - when NULL, the filter is skipped.';

-- ============================================================================
-- 5. RECREATE popular_recipes_mv with is_hidden filter
-- ============================================================================
-- Drop and recreate the materialized view with the new filter
DROP MATERIALIZED VIEW IF EXISTS public.popular_recipes_mv;

CREATE MATERIALIZED VIEW public.popular_recipes_mv AS
SELECT
    r.id,
    r.category_id,
    -- Popularity score: rating quality + engagement
    (COALESCE(r.average_rating, 0) * COALESCE(r.rating_count, 0)) +
    COALESCE(r.total_times_cooked, 0) AS popularity_score,
    -- Rank within each category (for category filtering)
    ROW_NUMBER() OVER (
        PARTITION BY r.category_id
        ORDER BY (COALESCE(r.average_rating, 0) * COALESCE(r.rating_count, 0)) +
                 COALESCE(r.total_times_cooked, 0) DESC,
                 r.created_at DESC
    ) AS category_rank,
    -- Global rank across all recipes (for "All" view)
    ROW_NUMBER() OVER (
        ORDER BY (COALESCE(r.average_rating, 0) * COALESCE(r.rating_count, 0)) +
                 COALESCE(r.total_times_cooked, 0) DESC,
                 r.created_at DESC
    ) AS global_rank
FROM public.recipes r
WHERE r.is_public = TRUE
  AND r.is_draft = FALSE
  AND r.is_hidden = FALSE;  -- NEW: exclude hidden recipes

-- Recreate indexes (required for CONCURRENTLY refresh)
CREATE UNIQUE INDEX IF NOT EXISTS idx_popular_recipes_mv_id
    ON public.popular_recipes_mv(id);

CREATE INDEX IF NOT EXISTS idx_popular_recipes_mv_category
    ON public.popular_recipes_mv(category_id, category_rank);

CREATE INDEX IF NOT EXISTS idx_popular_recipes_mv_global
    ON public.popular_recipes_mv(global_rank);

COMMENT ON MATERIALIZED VIEW public.popular_recipes_mv IS
'Cached popularity rankings for recipes. Refreshed every 4 hours.
Contains pre-computed popularity_score, category_rank, and global_rank.
Excludes hidden recipes (moderated content). Used by get_popular_recipes().';

-- ============================================================================
-- 6. Refresh the materialized view with the new data
-- ============================================================================
REFRESH MATERIALIZED VIEW public.popular_recipes_mv;
