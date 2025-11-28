-- Migration: Add collections system and draft recipes
-- Created: 2025-01-27
-- Description: Replaces user_saved_recipes with proper collections system.
--              Adds is_draft flag to recipes for extract-then-save flow.

-- ============================================================================
-- OVERVIEW
-- ============================================================================
-- This migration implements:
-- 1. user_collections: Personal recipe collections for each user
-- 2. collection_recipes: Many-to-many link between collections and recipes
-- 3. is_draft column on recipes: Draft vs published state
-- 4. recipe_id column on extraction_jobs: Links job to created draft recipe
-- 5. Trigger to create default collections on user signup
-- 6. Migration of existing user_saved_recipes to new collections system

-- ============================================================================
-- USER COLLECTIONS TABLE
-- ============================================================================

CREATE TABLE user_collections (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,

    -- Collection info
    name VARCHAR(100) NOT NULL,
    slug VARCHAR(100) NOT NULL,  -- URL-friendly name (e.g., 'extracted', 'saved')
    description TEXT,

    -- System collections can't be deleted/renamed
    is_system BOOLEAN NOT NULL DEFAULT false,

    -- Ordering
    sort_order INTEGER NOT NULL DEFAULT 0,

    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    UNIQUE(user_id, slug)
);

COMMENT ON TABLE user_collections IS
'Personal recipe collections for each user. System collections (extracted, saved) are created automatically.';

COMMENT ON COLUMN user_collections.slug IS
'URL-friendly identifier for the collection (unique per user)';

COMMENT ON COLUMN user_collections.is_system IS
'System collections (extracted, saved) cannot be deleted or renamed';

-- Indexes
CREATE INDEX idx_user_collections_user ON user_collections(user_id);
CREATE INDEX idx_user_collections_user_sort ON user_collections(user_id, sort_order);

-- Trigger for updated_at
CREATE TRIGGER update_user_collections_updated_at BEFORE UPDATE ON user_collections
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- ============================================================================
-- COLLECTION RECIPES TABLE
-- ============================================================================

CREATE TABLE collection_recipes (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    collection_id UUID NOT NULL REFERENCES user_collections(id) ON DELETE CASCADE,
    recipe_id UUID NOT NULL REFERENCES recipes(id) ON DELETE CASCADE,

    -- Ordering within collection
    sort_order INTEGER NOT NULL DEFAULT 0,

    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    UNIQUE(collection_id, recipe_id)
);

COMMENT ON TABLE collection_recipes IS
'Many-to-many relationship between collections and recipes. A recipe can be in multiple collections.';

-- Indexes
CREATE INDEX idx_collection_recipes_collection ON collection_recipes(collection_id);
CREATE INDEX idx_collection_recipes_recipe ON collection_recipes(recipe_id);
CREATE INDEX idx_collection_recipes_collection_sort ON collection_recipes(collection_id, sort_order);

-- ============================================================================
-- MODIFY RECIPES TABLE - ADD IS_DRAFT
-- ============================================================================

-- Add is_draft column for extract-then-save flow
ALTER TABLE recipes
ADD COLUMN is_draft BOOLEAN NOT NULL DEFAULT false;

COMMENT ON COLUMN recipes.is_draft IS
'Draft recipes are only visible to owner and not counted toward quotas. Set to false when user saves.';

-- Partial index for filtering out drafts in queries (most queries want published only)
CREATE INDEX idx_recipes_is_draft ON recipes(is_draft) WHERE is_draft = false;

-- ============================================================================
-- MODIFY EXTRACTION_JOBS TABLE - ADD RECIPE_ID
-- ============================================================================

-- Add recipe_id to link extraction job to created draft recipe
ALTER TABLE extraction_jobs
ADD COLUMN recipe_id UUID REFERENCES recipes(id) ON DELETE SET NULL;

COMMENT ON COLUMN extraction_jobs.recipe_id IS
'Reference to the draft recipe created by this extraction job';

CREATE INDEX idx_extraction_jobs_recipe ON extraction_jobs(recipe_id);

-- ============================================================================
-- ROW LEVEL SECURITY (RLS)
-- ============================================================================

-- Enable RLS on new tables
ALTER TABLE user_collections ENABLE ROW LEVEL SECURITY;
ALTER TABLE collection_recipes ENABLE ROW LEVEL SECURITY;

-- user_collections policies (users see only their own)
CREATE POLICY "Users can view their own collections"
ON user_collections FOR SELECT
USING (auth.uid() = user_id);

CREATE POLICY "Users can insert their own collections"
ON user_collections FOR INSERT
WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update their own non-system collections"
ON user_collections FOR UPDATE
USING (auth.uid() = user_id AND is_system = false);

CREATE POLICY "Users can delete their own non-system collections"
ON user_collections FOR DELETE
USING (auth.uid() = user_id AND is_system = false);

-- collection_recipes policies (based on collection ownership)
CREATE POLICY "Users can view recipes in their collections"
ON collection_recipes FOR SELECT
USING (
    EXISTS (
        SELECT 1 FROM user_collections
        WHERE user_collections.id = collection_recipes.collection_id
        AND user_collections.user_id = auth.uid()
    )
);

CREATE POLICY "Users can add recipes to their collections"
ON collection_recipes FOR INSERT
WITH CHECK (
    EXISTS (
        SELECT 1 FROM user_collections
        WHERE user_collections.id = collection_recipes.collection_id
        AND user_collections.user_id = auth.uid()
    )
);

CREATE POLICY "Users can remove recipes from their collections"
ON collection_recipes FOR DELETE
USING (
    EXISTS (
        SELECT 1 FROM user_collections
        WHERE user_collections.id = collection_recipes.collection_id
        AND user_collections.user_id = auth.uid()
    )
);

-- Update recipes RLS to handle drafts (owner sees drafts, others don't)
-- Drop existing select policy and create new one that handles drafts
DROP POLICY IF EXISTS "Anyone can view public recipes" ON recipes;
DROP POLICY IF EXISTS "Users can view their own recipes" ON recipes;

CREATE POLICY "View public non-draft recipes"
ON recipes FOR SELECT
USING (is_public = true AND is_draft = false);

CREATE POLICY "Users can view their own recipes including drafts"
ON recipes FOR SELECT
USING (created_by = auth.uid());

-- ============================================================================
-- FUNCTIONS
-- ============================================================================

-- Function to create default collections for a user
CREATE OR REPLACE FUNCTION create_default_collections(p_user_id UUID)
RETURNS void AS $$
BEGIN
    -- Create "Extracted" collection
    INSERT INTO user_collections (user_id, name, slug, is_system, sort_order)
    VALUES (p_user_id, 'Extracted', 'extracted', true, 0)
    ON CONFLICT (user_id, slug) DO NOTHING;

    -- Create "Saved" collection
    INSERT INTO user_collections (user_id, name, slug, is_system, sort_order)
    VALUES (p_user_id, 'Saved', 'saved', true, 1)
    ON CONFLICT (user_id, slug) DO NOTHING;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

COMMENT ON FUNCTION create_default_collections IS
'Creates the default system collections (Extracted, Saved) for a new user';

-- Function to get user collection by slug (returns ID)
CREATE OR REPLACE FUNCTION get_user_collection_id(p_user_id UUID, p_slug VARCHAR(100))
RETURNS UUID AS $$
DECLARE
    v_collection_id UUID;
BEGIN
    SELECT id INTO v_collection_id
    FROM user_collections
    WHERE user_id = p_user_id AND slug = p_slug;

    RETURN v_collection_id;
END;
$$ LANGUAGE plpgsql STABLE;

COMMENT ON FUNCTION get_user_collection_id IS
'Gets the collection ID for a user by slug';

-- ============================================================================
-- TRIGGER: CREATE DEFAULT COLLECTIONS ON USER SIGNUP
-- ============================================================================

-- Trigger function that creates collections when a user profile is created
CREATE OR REPLACE FUNCTION trigger_create_default_collections()
RETURNS TRIGGER AS $$
BEGIN
    PERFORM create_default_collections(NEW.id);
    RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Trigger on users table (fires when profile is created)
CREATE TRIGGER on_user_created_create_collections
    AFTER INSERT ON public.users
    FOR EACH ROW
    EXECUTE FUNCTION trigger_create_default_collections();

-- ============================================================================
-- MIGRATE EXISTING DATA
-- ============================================================================

-- Create default collections for all existing users
DO $$
DECLARE
    user_record RECORD;
BEGIN
    FOR user_record IN SELECT id FROM public.users LOOP
        PERFORM create_default_collections(user_record.id);
    END LOOP;
END $$;

-- Migrate user_saved_recipes to collection_recipes
-- Map 'extracted' source to 'extracted' collection
-- Map 'saved' and 'forked' source to 'saved' collection
INSERT INTO collection_recipes (collection_id, recipe_id, created_at)
SELECT
    (SELECT id FROM user_collections WHERE user_id = usr.user_id AND slug = CASE
        WHEN usr.source = 'extracted' THEN 'extracted'
        ELSE 'saved'
    END),
    usr.recipe_id,
    usr.created_at
FROM user_saved_recipes usr
ON CONFLICT (collection_id, recipe_id) DO NOTHING;

-- ============================================================================
-- CLEANUP OLD TABLE (OPTIONAL - KEEP FOR NOW AS BACKUP)
-- ============================================================================

-- We'll keep user_saved_recipes for now as a backup
-- Can be dropped in a future migration after verifying data integrity
-- DROP TABLE IF EXISTS user_saved_recipes;

-- ============================================================================
-- VERIFICATION
-- ============================================================================

DO $$
BEGIN
    -- Check user_collections
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.tables
        WHERE table_name = 'user_collections'
    ) THEN
        RAISE EXCEPTION 'Migration failed: user_collections table not created';
    END IF;

    -- Check collection_recipes
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.tables
        WHERE table_name = 'collection_recipes'
    ) THEN
        RAISE EXCEPTION 'Migration failed: collection_recipes table not created';
    END IF;

    -- Check is_draft column
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'recipes' AND column_name = 'is_draft'
    ) THEN
        RAISE EXCEPTION 'Migration failed: is_draft column not added to recipes';
    END IF;

    -- Check recipe_id column on extraction_jobs
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'extraction_jobs' AND column_name = 'recipe_id'
    ) THEN
        RAISE EXCEPTION 'Migration failed: recipe_id column not added to extraction_jobs';
    END IF;

    RAISE NOTICE 'Migration successful: Collections system and draft recipes implemented';
END $$;
