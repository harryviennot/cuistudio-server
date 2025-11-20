-- Migration: Add PostgreSQL function for full-text recipe search
-- Created: 2025-01-30
-- Description: Creates RPC function for searching recipes with ts_rank relevance scoring
-- This function is called from the RecipeRepository to perform language-aware searches

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
  created_at timestamptz,
  rank real
) AS $$
BEGIN
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
    r.created_at,
    -- Calculate relevance score using ts_rank
    -- Higher score = more relevant result
    ts_rank(r.search_vector, plainto_tsquery('simple', search_query)) as rank
  FROM recipes r
  WHERE
    -- Match search query against search vector
    r.search_vector @@ plainto_tsquery('simple', search_query)
    AND (
      -- Include public recipes OR user's own recipes
      r.is_public = true
      OR (user_id_param IS NOT NULL AND r.created_by = user_id_param)
    )
  ORDER BY rank DESC, r.created_at DESC
  LIMIT limit_param
  OFFSET offset_param;
END;
$$ LANGUAGE plpgsql STABLE;

-- Add comment for documentation
COMMENT ON FUNCTION search_recipes_full_text IS
'Full-text search function for recipes with relevance ranking. Uses plainto_tsquery for natural language queries and ts_rank for scoring. Results are sorted by relevance (highest first), then by creation date.';
