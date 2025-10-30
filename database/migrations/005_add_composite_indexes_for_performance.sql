-- Migration: Add composite indexes for performance optimization
-- Created: 2025-01-30
-- Description: Adds composite indexes to optimize common query patterns

-- Composite index for fetching user's recipes sorted by date
-- This optimizes the common query: SELECT ... WHERE created_by = ? ORDER BY created_at DESC
-- Allows PostgreSQL to use index-only scan instead of separate filter + sort
CREATE INDEX IF NOT EXISTS idx_recipes_user_sort
ON recipes(created_by, created_at DESC);

-- Composite index for public recipes sorted by date
-- This optimizes: SELECT ... WHERE is_public = true ORDER BY created_at DESC
CREATE INDEX IF NOT EXISTS idx_recipes_public_sort
ON recipes(is_public, created_at DESC);

-- Index on user_recipe_data for batch fetching user data by recipe IDs
-- This optimizes: SELECT ... WHERE user_id = ? AND recipe_id IN (...)
CREATE INDEX IF NOT EXISTS idx_user_recipe_data_batch
ON user_recipe_data(user_id, recipe_id);

-- Comments explaining the optimization
COMMENT ON INDEX idx_recipes_user_sort IS
'Composite index for efficient user recipes query with date sorting. Eliminates need for separate filter and sort operations.';

COMMENT ON INDEX idx_recipes_public_sort IS
'Composite index for efficient public recipes query with date sorting.';

COMMENT ON INDEX idx_user_recipe_data_batch IS
'Composite index for batch fetching user data for multiple recipes, eliminating N+1 query problem.';
