-- Migration: Add video extraction support with duplicate detection
-- Created: 2025-01-27
-- Description: Creates tables for video source tracking, creator attribution, and user recipe collections
--              Enables duplicate detection for video URLs and separates extraction from saving

-- ============================================================================
-- OVERVIEW
-- ============================================================================
-- This migration implements:
-- 1. user_saved_recipes: Links users to recipes in their collection
-- 2. video_creators: Stores video content creators for attribution
-- 3. video_sources: Links recipes to source videos for duplicate detection
-- 4. extracted_data column on extraction_jobs: Stores extraction results before save
-- 5. image_source column on recipes: Tracks where the recipe image came from

-- ============================================================================
-- USER SAVED RECIPES TABLE
-- ============================================================================

CREATE TABLE user_saved_recipes (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    recipe_id UUID NOT NULL REFERENCES recipes(id) ON DELETE CASCADE,

    -- How the user got this recipe
    source VARCHAR(20) NOT NULL CHECK (source IN ('extracted', 'saved', 'forked')),

    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    UNIQUE(user_id, recipe_id)
);

COMMENT ON TABLE user_saved_recipes IS
'Links users to recipes in their collection. Tracks how each recipe was added (extracted, saved from another user, or forked).';

COMMENT ON COLUMN user_saved_recipes.source IS
'How the user acquired this recipe: extracted (they extracted it), saved (added existing recipe), forked (created a fork)';

-- Indexes
CREATE INDEX idx_user_saved_recipes_user ON user_saved_recipes(user_id);
CREATE INDEX idx_user_saved_recipes_recipe ON user_saved_recipes(recipe_id);
CREATE INDEX idx_user_saved_recipes_user_created ON user_saved_recipes(user_id, created_at DESC);

-- ============================================================================
-- VIDEO CREATORS TABLE
-- ============================================================================

CREATE TABLE video_creators (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),

    -- Platform identification (composite unique key)
    platform VARCHAR(20) NOT NULL CHECK (platform IN ('tiktok', 'youtube', 'instagram')),
    platform_user_id VARCHAR(255) NOT NULL,
    platform_username VARCHAR(255),

    -- Display information
    display_name VARCHAR(255),
    profile_url TEXT,
    avatar_url TEXT,

    -- Claim status (when creator joins Cuistudio)
    claimed_by_user_id UUID REFERENCES auth.users(id) ON DELETE SET NULL,
    claimed_at TIMESTAMP WITH TIME ZONE,

    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    UNIQUE(platform, platform_user_id)
);

COMMENT ON TABLE video_creators IS
'Stores video content creators from TikTok, YouTube, Instagram for attribution. Supports ownership claiming when creators join Cuistudio.';

COMMENT ON COLUMN video_creators.platform_user_id IS
'Stable user ID from the platform (channel_id for YouTube, user_id for TikTok/Instagram)';

COMMENT ON COLUMN video_creators.platform_username IS
'Current username/handle on the platform (can change over time)';

COMMENT ON COLUMN video_creators.claimed_by_user_id IS
'Cuistudio user ID when the creator claims ownership of their content';

-- Indexes
CREATE INDEX idx_video_creators_platform_lookup ON video_creators(platform, platform_user_id);
CREATE INDEX idx_video_creators_platform_username ON video_creators(platform, platform_username);
CREATE INDEX idx_video_creators_claimed_by ON video_creators(claimed_by_user_id);

-- Trigger for updated_at
CREATE TRIGGER update_video_creators_updated_at BEFORE UPDATE ON video_creators
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- ============================================================================
-- VIDEO SOURCES TABLE
-- ============================================================================

CREATE TABLE video_sources (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),

    -- Video identification (composite unique key for dedup)
    platform VARCHAR(20) NOT NULL CHECK (platform IN ('tiktok', 'youtube', 'instagram')),
    platform_video_id VARCHAR(255) NOT NULL,

    -- URLs
    original_url TEXT NOT NULL,
    canonical_url TEXT,

    -- Video metadata from yt-dlp
    title VARCHAR(500),
    description TEXT,
    duration_seconds INTEGER,
    thumbnail_url TEXT,
    view_count BIGINT,
    like_count BIGINT,
    upload_date DATE,

    -- References
    video_creator_id UUID REFERENCES video_creators(id) ON DELETE SET NULL,
    recipe_id UUID NOT NULL REFERENCES recipes(id) ON DELETE CASCADE,

    -- Store raw yt-dlp output for future use
    raw_metadata JSONB,

    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    UNIQUE(platform, platform_video_id)
);

COMMENT ON TABLE video_sources IS
'Links recipes to their source videos. Enables duplicate detection by platform + video_id lookup.';

COMMENT ON COLUMN video_sources.platform_video_id IS
'Video ID from the platform (used with platform for duplicate detection)';

COMMENT ON COLUMN video_sources.raw_metadata IS
'Full yt-dlp output stored for future use or debugging';

-- Indexes
CREATE INDEX idx_video_sources_recipe ON video_sources(recipe_id);
CREATE INDEX idx_video_sources_lookup ON video_sources(platform, platform_video_id);
CREATE INDEX idx_video_sources_creator ON video_sources(video_creator_id);

-- ============================================================================
-- MODIFY EXTRACTION_JOBS TABLE
-- ============================================================================

-- Add column to store extraction result before user saves
ALTER TABLE extraction_jobs
ADD COLUMN extracted_data JSONB;

COMMENT ON COLUMN extraction_jobs.extracted_data IS
'Stores the extracted recipe data until user saves. Cleared after save or auto-expires.';

-- Add column to track if this was a duplicate detection (video already extracted)
ALTER TABLE extraction_jobs
ADD COLUMN existing_recipe_id UUID REFERENCES recipes(id) ON DELETE SET NULL;

COMMENT ON COLUMN extraction_jobs.existing_recipe_id IS
'If set, indicates a duplicate video was detected and this is the existing recipe ID';

-- Add video metadata storage
ALTER TABLE extraction_jobs
ADD COLUMN video_metadata JSONB;

COMMENT ON COLUMN extraction_jobs.video_metadata IS
'Stores video-specific metadata (platform, video_id, creator info) for video extractions';

-- ============================================================================
-- MODIFY RECIPES TABLE
-- ============================================================================

-- Add column to track image source
ALTER TABLE recipes
ADD COLUMN image_source VARCHAR(20) CHECK (image_source IN ('generated', 'video_thumbnail', 'user_upload', 'scraped'));

COMMENT ON COLUMN recipes.image_source IS
'Tracks the origin of the recipe image: generated (AI), video_thumbnail, user_upload, or scraped (from URL)';

-- ============================================================================
-- ROW LEVEL SECURITY (RLS)
-- ============================================================================

-- Enable RLS on new tables
ALTER TABLE user_saved_recipes ENABLE ROW LEVEL SECURITY;
ALTER TABLE video_creators ENABLE ROW LEVEL SECURITY;
ALTER TABLE video_sources ENABLE ROW LEVEL SECURITY;

-- user_saved_recipes policies
CREATE POLICY "Users can view their own saved recipes"
ON user_saved_recipes FOR SELECT
USING (auth.uid() = user_id);

CREATE POLICY "Users can insert their own saved recipes"
ON user_saved_recipes FOR INSERT
WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can delete their own saved recipes"
ON user_saved_recipes FOR DELETE
USING (auth.uid() = user_id);

-- video_creators policies (public read, system write)
CREATE POLICY "Anyone can view video creators"
ON video_creators FOR SELECT
USING (true);

-- video_sources policies (view if recipe is accessible)
CREATE POLICY "View video sources for public recipes"
ON video_sources FOR SELECT
USING (
    EXISTS (
        SELECT 1 FROM recipes
        WHERE recipes.id = video_sources.recipe_id
        AND recipes.is_public = true
    )
);

CREATE POLICY "View video sources for own recipes"
ON video_sources FOR SELECT
USING (
    EXISTS (
        SELECT 1 FROM recipes
        WHERE recipes.id = video_sources.recipe_id
        AND recipes.created_by = auth.uid()
    )
);

-- ============================================================================
-- HELPER FUNCTIONS
-- ============================================================================

-- Function to check if a video has already been extracted
CREATE OR REPLACE FUNCTION check_video_duplicate(
    p_platform VARCHAR(20),
    p_platform_video_id VARCHAR(255)
)
RETURNS TABLE (
    recipe_id UUID,
    is_public BOOLEAN,
    created_by UUID
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        vs.recipe_id,
        r.is_public,
        r.created_by
    FROM video_sources vs
    INNER JOIN recipes r ON r.id = vs.recipe_id
    WHERE vs.platform = p_platform
    AND vs.platform_video_id = p_platform_video_id;
END;
$$ LANGUAGE plpgsql STABLE;

COMMENT ON FUNCTION check_video_duplicate IS
'Checks if a video has already been extracted. Returns recipe info if found.';

-- Function to get or create a video creator
CREATE OR REPLACE FUNCTION get_or_create_video_creator(
    p_platform VARCHAR(20),
    p_platform_user_id VARCHAR(255),
    p_platform_username VARCHAR(255) DEFAULT NULL,
    p_display_name VARCHAR(255) DEFAULT NULL,
    p_profile_url TEXT DEFAULT NULL
)
RETURNS UUID AS $$
DECLARE
    v_creator_id UUID;
BEGIN
    -- Try to find existing creator
    SELECT id INTO v_creator_id
    FROM video_creators
    WHERE platform = p_platform AND platform_user_id = p_platform_user_id;

    -- If not found, create new
    IF v_creator_id IS NULL THEN
        INSERT INTO video_creators (platform, platform_user_id, platform_username, display_name, profile_url)
        VALUES (p_platform, p_platform_user_id, p_platform_username, p_display_name, p_profile_url)
        RETURNING id INTO v_creator_id;
    ELSE
        -- Update username/display_name if changed
        UPDATE video_creators
        SET
            platform_username = COALESCE(p_platform_username, platform_username),
            display_name = COALESCE(p_display_name, display_name),
            profile_url = COALESCE(p_profile_url, profile_url),
            updated_at = NOW()
        WHERE id = v_creator_id
        AND (
            platform_username IS DISTINCT FROM p_platform_username
            OR display_name IS DISTINCT FROM p_display_name
            OR profile_url IS DISTINCT FROM p_profile_url
        );
    END IF;

    RETURN v_creator_id;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION get_or_create_video_creator IS
'Gets existing video creator or creates new one. Updates metadata if creator exists but info changed.';

-- ============================================================================
-- BACKFILL EXISTING RECIPES TO USER COLLECTIONS
-- ============================================================================

-- Add all existing recipes to their creators' collections
INSERT INTO user_saved_recipes (user_id, recipe_id, source)
SELECT created_by, id, 'extracted'
FROM recipes
ON CONFLICT (user_id, recipe_id) DO NOTHING;

-- ============================================================================
-- VERIFICATION
-- ============================================================================

DO $$
BEGIN
    -- Check user_saved_recipes
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.tables
        WHERE table_name = 'user_saved_recipes'
    ) THEN
        RAISE EXCEPTION 'Migration failed: user_saved_recipes table not created';
    END IF;

    -- Check video_creators
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.tables
        WHERE table_name = 'video_creators'
    ) THEN
        RAISE EXCEPTION 'Migration failed: video_creators table not created';
    END IF;

    -- Check video_sources
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.tables
        WHERE table_name = 'video_sources'
    ) THEN
        RAISE EXCEPTION 'Migration failed: video_sources table not created';
    END IF;

    -- Check extracted_data column
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'extraction_jobs' AND column_name = 'extracted_data'
    ) THEN
        RAISE EXCEPTION 'Migration failed: extracted_data column not added to extraction_jobs';
    END IF;

    -- Check image_source column
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'recipes' AND column_name = 'image_source'
    ) THEN
        RAISE EXCEPTION 'Migration failed: image_source column not added to recipes';
    END IF;

    RAISE NOTICE 'Migration successful: Video extraction support tables and columns created';
END $$;
