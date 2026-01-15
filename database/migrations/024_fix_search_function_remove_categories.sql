-- Migration: Fix search_recipes_full_text function to remove deprecated categories column
-- Date: 2025-01-15
-- Reason: The search_recipes_full_text function references r.categories which was dropped in migration 018
--         Replace with category_id which is the current schema

-- Must drop first because return type is changing
DROP FUNCTION IF EXISTS public.search_recipes_full_text(text, uuid, integer, integer);

-- Recreate the function with updated return type
CREATE FUNCTION public.search_recipes_full_text(
    search_query text,
    user_id_param uuid DEFAULT NULL::uuid,
    limit_param integer DEFAULT 20,
    offset_param integer DEFAULT 0
)
RETURNS TABLE(
    id uuid,
    title character varying,
    description text,
    image_url text,
    servings integer,
    difficulty character varying,
    tags text[],
    category_id uuid,  -- Changed from categories text[]
    prep_time_minutes integer,
    cook_time_minutes integer,
    total_time_minutes integer,
    resting_time_minutes integer,  -- Added resting time
    created_by uuid,
    is_public boolean,
    fork_count integer,
    average_rating numeric,
    rating_count integer,
    total_times_cooked integer,
    created_at timestamp with time zone,
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
    r.category_id,  -- Changed from r.categories
    r.prep_time_minutes,
    r.cook_time_minutes,
    r.total_time_minutes,
    r.resting_time_minutes,  -- Added resting time
    r.created_by,
    r.is_public,
    r.fork_count,
    r.average_rating,
    r.rating_count,
    r.total_times_cooked,
    r.created_at,
    -- Use ts_rank_cd for better ranking with normalization
    ts_rank_cd(r.search_vector, query_tsquery, 32) as rank
  FROM recipes r
  WHERE
    -- Use GIN index for fast search
    r.search_vector @@ query_tsquery
    AND (
      -- Use index for public/user filtering
      r.is_public = true
      OR (user_id_param IS NOT NULL AND r.created_by = user_id_param)
    )
  ORDER BY rank DESC, r.created_at DESC
  LIMIT limit_param
  OFFSET offset_param;
END;
$$;

COMMENT ON FUNCTION public.search_recipes_full_text(search_query text, user_id_param uuid, limit_param integer, offset_param integer)
IS 'Full-text search function for recipes with ranking and aggregated metrics (ratings, cooked count). Returns recipes sorted by relevance. Updated to use category_id instead of deprecated categories array.';
