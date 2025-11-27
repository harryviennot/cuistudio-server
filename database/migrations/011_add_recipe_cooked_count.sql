-- Migration: Add recipe cooked count aggregation
-- Created: 2025-01-27
-- Description: Adds total_times_cooked field to recipes table with automatic updates
--              via database trigger when users mark recipes as cooked

-- ============================================================================
-- OVERVIEW
-- ============================================================================
-- This migration enables tracking of how many times a recipe has been cooked
-- by all users (global count), separate from personal cooking counts.
--
-- Changes to recipes table:
-- - Adds total_times_cooked: INTEGER field tracking global cooking count
-- - Adds index for efficient sorting by popularity
--
-- Trigger functionality:
-- - Automatically increments recipes.total_times_cooked when a user cooks a recipe
-- - Runs asynchronously after user_recipe_data.times_cooked is updated
-- - Ensures consistency without blocking API responses
--
-- Data distinction:
-- - user_recipe_data.times_cooked = Personal count (how many times I cooked this)
-- - recipes.total_times_cooked = Global count (how many times everyone cooked this)

-- ============================================================================
-- SCHEMA CHANGES
-- ============================================================================

-- Add total_times_cooked column to recipes table
-- Stores the aggregate count of times this recipe has been cooked by all users
ALTER TABLE recipes
ADD COLUMN total_times_cooked INTEGER DEFAULT 0 CHECK (total_times_cooked >= 0);

COMMENT ON COLUMN recipes.total_times_cooked IS
'Total number of times this recipe has been cooked by all users. Updated automatically via trigger when user_recipe_data.times_cooked changes.';

-- ============================================================================
-- INDEXES
-- ============================================================================

-- Index for filtering/sorting recipes by cooking popularity
-- Supports queries like "get most cooked recipes" or "recipes cooked more than 100 times"
CREATE INDEX IF NOT EXISTS idx_recipes_total_times_cooked
ON recipes(total_times_cooked DESC);

COMMENT ON INDEX idx_recipes_total_times_cooked IS
'Supports efficient sorting and filtering of recipes by cooking popularity (total_times_cooked). Enables "most popular" queries.';

-- ============================================================================
-- TRIGGER FUNCTION
-- ============================================================================

-- Function to update recipes.total_times_cooked when user_recipe_data.times_cooked changes
-- This runs automatically whenever a user marks a recipe as cooked
CREATE OR REPLACE FUNCTION update_recipe_cooked_count()
RETURNS TRIGGER AS $$
DECLARE
  cooked_delta INTEGER;
BEGIN
  -- Calculate the change in times_cooked
  IF TG_OP = 'INSERT' THEN
    -- New user_recipe_data record created
    cooked_delta := COALESCE(NEW.times_cooked, 0);
  ELSIF TG_OP = 'UPDATE' THEN
    -- Existing record updated
    cooked_delta := COALESCE(NEW.times_cooked, 0) - COALESCE(OLD.times_cooked, 0);
  ELSIF TG_OP = 'DELETE' THEN
    -- Record deleted (edge case)
    cooked_delta := -COALESCE(OLD.times_cooked, 0);
  END IF;

  -- Only update if there's an actual change
  IF cooked_delta != 0 THEN
    UPDATE recipes
    SET total_times_cooked = GREATEST(total_times_cooked + cooked_delta, 0)
    WHERE id = COALESCE(NEW.recipe_id, OLD.recipe_id);
  END IF;

  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION update_recipe_cooked_count IS
'Trigger function that automatically updates recipes.total_times_cooked when user_recipe_data.times_cooked changes. Handles INSERT, UPDATE, and DELETE operations.';

-- ============================================================================
-- TRIGGER
-- ============================================================================

-- Create trigger that fires after user_recipe_data.times_cooked is modified
DROP TRIGGER IF EXISTS trigger_update_recipe_cooked_count ON user_recipe_data;

CREATE TRIGGER trigger_update_recipe_cooked_count
AFTER INSERT OR UPDATE OF times_cooked OR DELETE ON user_recipe_data
FOR EACH ROW
EXECUTE FUNCTION update_recipe_cooked_count();

COMMENT ON TRIGGER trigger_update_recipe_cooked_count ON user_recipe_data IS
'Automatically updates recipes.total_times_cooked when a user marks a recipe as cooked. Fires after INSERT, UPDATE, or DELETE on user_recipe_data.times_cooked.';

-- ============================================================================
-- DATA BACKFILL
-- ============================================================================

-- Backfill total_times_cooked for existing recipes
-- Aggregates current user_recipe_data.times_cooked values
UPDATE recipes r
SET total_times_cooked = COALESCE(
  (
    SELECT SUM(times_cooked)
    FROM user_recipe_data urd
    WHERE urd.recipe_id = r.id
  ),
  0
);

-- ============================================================================
-- VERIFICATION QUERIES
-- ============================================================================

-- Verify column was added successfully
DO $$
BEGIN
  -- Check if column exists
  IF NOT EXISTS (
    SELECT 1 FROM information_schema.columns
    WHERE table_name = 'recipes' AND column_name = 'total_times_cooked'
  ) THEN
    RAISE EXCEPTION 'Migration failed: total_times_cooked column not created';
  END IF;

  -- Check if index exists
  IF NOT EXISTS (
    SELECT 1 FROM pg_indexes
    WHERE tablename = 'recipes' AND indexname = 'idx_recipes_total_times_cooked'
  ) THEN
    RAISE EXCEPTION 'Migration failed: idx_recipes_total_times_cooked index not created';
  END IF;

  -- Check if trigger exists
  IF NOT EXISTS (
    SELECT 1 FROM pg_trigger
    WHERE tgname = 'trigger_update_recipe_cooked_count'
  ) THEN
    RAISE EXCEPTION 'Migration failed: trigger_update_recipe_cooked_count not created';
  END IF;

  RAISE NOTICE 'Migration successful: total_times_cooked column, index, and trigger created';
END $$;

-- Sample query to verify backfill worked correctly
-- Uncomment to run:
-- SELECT
--   r.id,
--   r.title,
--   r.total_times_cooked,
--   (SELECT COUNT(*) FROM user_recipe_data WHERE recipe_id = r.id) as user_count,
--   (SELECT SUM(times_cooked) FROM user_recipe_data WHERE recipe_id = r.id) as manual_sum
-- FROM recipes r
-- WHERE total_times_cooked > 0
-- LIMIT 10;

-- Test trigger functionality
-- Uncomment to test:
-- BEGIN;
-- -- Insert test data
-- INSERT INTO user_recipe_data (user_id, recipe_id, times_cooked)
-- VALUES ('test-user-id', 'test-recipe-id', 5);
-- -- Check if recipes.total_times_cooked was incremented by 5
-- SELECT total_times_cooked FROM recipes WHERE id = 'test-recipe-id';
-- ROLLBACK;
