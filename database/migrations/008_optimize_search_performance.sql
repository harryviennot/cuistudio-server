-- Migration: Optimize search performance
-- Created: 2025-01-30
-- Description: Adds indexes and optimizes search function for faster queries

-- Add index on is_public for faster filtering
CREATE INDEX IF NOT EXISTS idx_recipes_is_public
ON recipes(is_public);

-- Add composite index for user-specific queries
CREATE INDEX IF NOT EXISTS idx_recipes_created_by_is_public
ON recipes(created_by, is_public);

-- Optimize search function to use simple dictionary for all searches
-- This matches how the search vectors are created and improves performance
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

-- Comments
COMMENT ON INDEX idx_recipes_is_public IS 'Index for fast filtering of public recipes';
COMMENT ON INDEX idx_recipes_created_by_is_public IS 'Composite index for user-specific recipe queries';
