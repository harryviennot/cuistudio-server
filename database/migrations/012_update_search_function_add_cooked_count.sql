-- Migration: Update search function to include total_times_cooked
-- Created: 2025-01-27
-- Description: Updates search_recipes_full_text function to return the new
--              total_times_cooked field along with rating aggregation fields

-- Update the search function to include rating and cooked count fields
CREATE OR REPLACE FUNCTION search_recipes_full_text(
  search_query text,
  user_id_param uuid DEFAULT NULL,
  limit_param integer DEFAULT 20,
  offset_param integer DEFAULT 0
)
RETURNS TABLE (
  id uuid,
  title varchar,
  description text,
  image_url text,
  servings integer,
  difficulty varchar,
  tags text[],
  categories text[],
  prep_time_minutes integer,
  cook_time_minutes integer,
  total_time_minutes integer,
  created_by uuid,
  is_public boolean,
  fork_count integer,
  average_rating decimal,
  rating_count integer,
  total_times_cooked integer,
  created_at timestamptz,
  rank real
) AS $$
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
    r.categories,
    r.prep_time_minutes,
    r.cook_time_minutes,
    r.total_time_minutes,
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
$$ LANGUAGE plpgsql STABLE;

COMMENT ON FUNCTION search_recipes_full_text IS
'Full-text search function for recipes with ranking and aggregated metrics (ratings, cooked count). Returns recipes sorted by relevance.';
