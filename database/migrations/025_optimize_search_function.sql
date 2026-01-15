-- Migration: Optimize search_recipes_full_text with database-side filtering
-- Date: 2025-01-15
-- Reason: Move filtering from Python to database for better performance
--         - Eliminates fetching 100 recipes then filtering in Python
--         - Fixes broken pagination (offset/limit now work correctly with filters)
--         - Adds source_type to return value for video source batching

-- Must drop first because signature is changing
DROP FUNCTION IF EXISTS public.search_recipes_full_text(text, uuid, integer, integer);

-- Recreate with filter parameters
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
    -- Access control
    AND (r.is_public = true OR (user_id_param IS NOT NULL AND r.created_by = user_id_param))
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

COMMENT ON FUNCTION public.search_recipes_full_text IS 'Optimized full-text search with database-side filtering. All filter parameters are optional - when NULL, the filter is skipped. Returns source_type for video source batching.';
