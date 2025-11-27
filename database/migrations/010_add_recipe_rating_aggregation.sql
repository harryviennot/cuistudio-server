-- Migration: Add recipe rating aggregation fields
-- Created: 2025-01-22
-- Description: Adds aggregate rating fields to recipes table to support rating display
--              and future recommendation algorithms

-- ============================================================================
-- OVERVIEW
-- ============================================================================
-- This migration enables half-star rating support and adds aggregate rating fields:
--
-- Changes to user_recipe_data table:
-- - Updates rating column from INTEGER to DECIMAL(2,1) to support half-stars
-- - Adds constraint to allow ratings: 0.5, 1.0, 1.5, 2.0, ..., 5.0
--
-- Additions to recipes table:
-- 1. average_rating: The mean rating across all user ratings (0.5-5.0 scale)
-- 2. rating_count: Total number of ratings received
-- 3. rating_distribution: JSONB object tracking count of each half-star rating level
--
-- These fields are updated automatically when users rate recipes via the
-- user_recipe_data table, enabling:
-- - Fast display of recipe ratings without aggregation queries
-- - Popularity metrics for sorting/filtering
-- - Rating distribution for UI (e.g., half-star breakdown charts)
-- - Data for future recommendation algorithms

-- ============================================================================
-- SCHEMA CHANGES
-- ============================================================================

-- First, update user_recipe_data to support half-star ratings
-- Change rating column from INTEGER to DECIMAL and update check constraint
ALTER TABLE user_recipe_data
ALTER COLUMN rating TYPE DECIMAL(2,1);

ALTER TABLE user_recipe_data
DROP CONSTRAINT IF EXISTS user_recipe_data_rating_check;

ALTER TABLE user_recipe_data
ADD CONSTRAINT user_recipe_data_rating_check
CHECK (rating IS NULL OR (rating >= 0.5 AND rating <= 5.0 AND (rating * 2) = FLOOR(rating * 2)));

COMMENT ON CONSTRAINT user_recipe_data_rating_check ON user_recipe_data IS
'Ensures rating is between 0.5 and 5.0 in half-star increments (0.5, 1.0, 1.5, ..., 5.0)';

-- Add average_rating column
-- Stores the calculated average of all user ratings (1.00 to 5.00)
-- NULL when recipe has no ratings yet
ALTER TABLE recipes
ADD COLUMN average_rating DECIMAL(3,2) CHECK (average_rating >= 1.00 AND average_rating <= 5.00);

COMMENT ON COLUMN recipes.average_rating IS
'Calculated average of all user ratings for this recipe. NULL if no ratings. Scale: 1.00-5.00';

-- Add rating_count column
-- Tracks total number of ratings received
ALTER TABLE recipes
ADD COLUMN rating_count INTEGER DEFAULT 0 CHECK (rating_count >= 0);

COMMENT ON COLUMN recipes.rating_count IS
'Total number of user ratings for this recipe. Used for popularity metrics and confidence in average_rating.';

-- Add rating_distribution column
-- JSONB object tracking count of each half-star rating level (0.5 to 5.0)
ALTER TABLE recipes
ADD COLUMN rating_distribution JSONB DEFAULT '{"0.5":0,"1":0,"1.5":0,"2":0,"2.5":0,"3":0,"3.5":0,"4":0,"4.5":0,"5":0}'::jsonb;

COMMENT ON COLUMN recipes.rating_distribution IS
'JSONB object tracking count of ratings at each half-star level (0.5-5.0). Format: {"0.5": count, "1": count, "1.5": count, ...}. Supports half-star ratings. Enables rating histogram display and detailed analytics.';

-- ============================================================================
-- INDEXES
-- ============================================================================

-- Index for filtering/sorting recipes by rating
-- Supports queries like "get top-rated recipes" or "recipes with rating > 4.0"
CREATE INDEX IF NOT EXISTS idx_recipes_average_rating
ON recipes(average_rating DESC NULLS LAST);

COMMENT ON INDEX idx_recipes_average_rating IS
'Supports efficient filtering and sorting of recipes by average rating. NULLS LAST ensures unrated recipes appear at the end.';

-- Composite index for tag-based recommendations with rating filter
-- Supports queries like "highly-rated Italian recipes"
CREATE INDEX IF NOT EXISTS idx_recipes_tags_rating
ON recipes USING GIN(tags)
WHERE average_rating >= 4.0;

COMMENT ON INDEX idx_recipes_tags_rating IS
'Partial index for tag-based searches filtered by high ratings (>= 4.0). Optimizes recommendation queries.';

-- ============================================================================
-- DATA INITIALIZATION
-- ============================================================================

-- Initialize rating fields for existing recipes
-- All existing recipes start with 0 ratings
UPDATE recipes
SET
  average_rating = NULL,
  rating_count = 0,
  rating_distribution = '{"0.5":0,"1":0,"1.5":0,"2":0,"2.5":0,"3":0,"3.5":0,"4":0,"4.5":0,"5":0}'::jsonb
WHERE average_rating IS NULL;

-- ============================================================================
-- HELPER FUNCTION (OPTIONAL)
-- ============================================================================

-- Function to calculate average rating from distribution (supports half-star ratings)
-- Useful for verification and recalculation if needed
CREATE OR REPLACE FUNCTION calculate_average_rating(distribution jsonb)
RETURNS DECIMAL(3,2) AS $$
DECLARE
  total_ratings INTEGER;
  weighted_sum DECIMAL;
BEGIN
  -- Calculate total number of ratings (all half-star levels)
  total_ratings :=
    (distribution->>'0.5')::INTEGER +
    (distribution->>'1')::INTEGER +
    (distribution->>'1.5')::INTEGER +
    (distribution->>'2')::INTEGER +
    (distribution->>'2.5')::INTEGER +
    (distribution->>'3')::INTEGER +
    (distribution->>'3.5')::INTEGER +
    (distribution->>'4')::INTEGER +
    (distribution->>'4.5')::INTEGER +
    (distribution->>'5')::INTEGER;

  -- Return NULL if no ratings
  IF total_ratings = 0 THEN
    RETURN NULL;
  END IF;

  -- Calculate weighted sum with half-star precision
  weighted_sum :=
    0.5 * (distribution->>'0.5')::INTEGER +
    1.0 * (distribution->>'1')::INTEGER +
    1.5 * (distribution->>'1.5')::INTEGER +
    2.0 * (distribution->>'2')::INTEGER +
    2.5 * (distribution->>'2.5')::INTEGER +
    3.0 * (distribution->>'3')::INTEGER +
    3.5 * (distribution->>'3.5')::INTEGER +
    4.0 * (distribution->>'4')::INTEGER +
    4.5 * (distribution->>'4.5')::INTEGER +
    5.0 * (distribution->>'5')::INTEGER;

  -- Return average rounded to 2 decimal places
  RETURN ROUND(weighted_sum::DECIMAL / total_ratings, 2);
END;
$$ LANGUAGE plpgsql IMMUTABLE;

COMMENT ON FUNCTION calculate_average_rating IS
'Helper function to calculate average rating from distribution JSONB with half-star support (0.5-5.0). Returns NULL if no ratings.';

-- ============================================================================
-- VERIFICATION QUERIES
-- ============================================================================

-- Verify columns were added successfully
-- Run after migration to confirm structure
DO $$
BEGIN
  -- Check if columns exist
  IF NOT EXISTS (
    SELECT 1 FROM information_schema.columns
    WHERE table_name = 'recipes' AND column_name = 'average_rating'
  ) THEN
    RAISE EXCEPTION 'Migration failed: average_rating column not created';
  END IF;

  IF NOT EXISTS (
    SELECT 1 FROM information_schema.columns
    WHERE table_name = 'recipes' AND column_name = 'rating_count'
  ) THEN
    RAISE EXCEPTION 'Migration failed: rating_count column not created';
  END IF;

  IF NOT EXISTS (
    SELECT 1 FROM information_schema.columns
    WHERE table_name = 'recipes' AND column_name = 'rating_distribution'
  ) THEN
    RAISE EXCEPTION 'Migration failed: rating_distribution column not created';
  END IF;

  RAISE NOTICE 'Migration successful: All rating aggregation columns created';
END $$;

-- Sample query to view rating data (will be all zeros for now)
-- Uncomment to run:
-- SELECT
--   id,
--   title,
--   average_rating,
--   rating_count,
--   rating_distribution
-- FROM recipes
-- LIMIT 5;
