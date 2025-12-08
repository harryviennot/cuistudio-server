-- Migration: Simplify Collections System
--
-- This migration replaces the user_collections + collection_recipes tables
-- with a simpler approach using user_recipe_data fields:
-- - was_extracted: true if user extracted this recipe (including duplicates)
-- - is_favorite: true if user favorited this recipe (already exists)
--
-- Virtual collections:
-- - "Extracted" = user_recipe_data WHERE was_extracted = true
-- - "Favorites" = user_recipe_data WHERE is_favorite = true

-- =============================================
-- STEP 1: Add was_extracted column
-- =============================================
ALTER TABLE user_recipe_data
ADD COLUMN IF NOT EXISTS was_extracted BOOLEAN NOT NULL DEFAULT false;

-- =============================================
-- STEP 2: Create indexes for efficient queries
-- =============================================

-- Partial index for extracted recipes (only indexes true values)
CREATE INDEX IF NOT EXISTS idx_user_recipe_data_extracted
ON user_recipe_data(user_id, created_at DESC)
WHERE was_extracted = true;

-- Partial index for favorite recipes (only indexes true values)
-- Note: idx_user_recipe_data_is_favorite already exists but isn't partial
CREATE INDEX IF NOT EXISTS idx_user_recipe_data_favorites
ON user_recipe_data(user_id, created_at DESC)
WHERE is_favorite = true;

-- =============================================
-- STEP 3: Migrate existing data
-- =============================================

-- Mark all recipes created by a user as "extracted" for that user
-- This handles the case where user created/extracted a recipe
INSERT INTO user_recipe_data (user_id, recipe_id, was_extracted, is_favorite, times_cooked)
SELECT
    r.created_by as user_id,
    r.id as recipe_id,
    true as was_extracted,
    false as is_favorite,
    0 as times_cooked
FROM recipes r
WHERE r.is_draft = false
  AND NOT EXISTS (
    SELECT 1 FROM user_recipe_data urd
    WHERE urd.user_id = r.created_by AND urd.recipe_id = r.id
  )
ON CONFLICT (user_id, recipe_id)
DO UPDATE SET was_extracted = true;

-- Migrate favorites from collection_recipes (saved collection)
-- This updates existing user_recipe_data records to mark them as favorites
UPDATE user_recipe_data urd
SET is_favorite = true
FROM collection_recipes cr
JOIN user_collections uc ON cr.collection_id = uc.id
WHERE uc.slug = 'saved'
  AND urd.user_id = uc.user_id
  AND urd.recipe_id = cr.recipe_id;

-- Also insert favorites that don't have user_recipe_data records yet
INSERT INTO user_recipe_data (user_id, recipe_id, was_extracted, is_favorite, times_cooked)
SELECT
    uc.user_id,
    cr.recipe_id,
    false as was_extracted,  -- Will be true if they also created it
    true as is_favorite,
    0 as times_cooked
FROM collection_recipes cr
JOIN user_collections uc ON cr.collection_id = uc.id
WHERE uc.slug = 'saved'
  AND NOT EXISTS (
    SELECT 1 FROM user_recipe_data urd
    WHERE urd.user_id = uc.user_id AND urd.recipe_id = cr.recipe_id
  )
ON CONFLICT (user_id, recipe_id)
DO UPDATE SET is_favorite = true;

-- =============================================
-- STEP 4: Drop old tables
-- NOTE: Run this AFTER verifying migration worked correctly
-- =============================================

-- Drop foreign key constraints first
ALTER TABLE collection_recipes DROP CONSTRAINT IF EXISTS collection_recipes_collection_id_fkey;
ALTER TABLE collection_recipes DROP CONSTRAINT IF EXISTS collection_recipes_recipe_id_fkey;

-- Drop the tables
DROP TABLE IF EXISTS collection_recipes;
DROP TABLE IF EXISTS user_collections;

-- =============================================
-- STEP 5: Update comments
-- =============================================
COMMENT ON COLUMN user_recipe_data.was_extracted IS
'True if this user extracted/imported this recipe. Used for the "Extracted" virtual collection.';

COMMENT ON COLUMN user_recipe_data.is_favorite IS
'True if this user favorited this recipe. Used for the "Favorites" virtual collection.';
