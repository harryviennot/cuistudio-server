-- Migration: Add recipe cooking events tracking
-- Created: 2025-01-27
-- Description: Creates recipe_cooking_events table to track every time a user cooks a recipe
--              Enables time-based queries like "most cooked this week" or trending recipes

-- ============================================================================
-- OVERVIEW
-- ============================================================================
-- This migration creates an event log table that records every cooking event.
-- Each time a user marks a recipe as cooked, we insert a new event with timestamp.
--
-- This enables:
-- - Time-based popularity queries ("most cooked in last 7 days")
-- - Trending recipe detection (recipes with increasing cook frequency)
-- - Cooking pattern analysis (seasonal trends, user behavior)
-- - Historical data preservation (vs overwriting last_cooked_at)
--
-- Data model:
-- - user_recipe_data.times_cooked = Personal cumulative count (how many times I cooked this)
-- - recipes.total_times_cooked = Global cumulative count (lifetime total)
-- - recipe_cooking_events = Event log (every cooking event with timestamp)

-- ============================================================================
-- SCHEMA
-- ============================================================================

-- Create recipe_cooking_events table
CREATE TABLE recipe_cooking_events (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    recipe_id UUID NOT NULL REFERENCES recipes(id) ON DELETE CASCADE,
    cooked_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    -- Optional: Could add additional context in the future
    -- cooking_duration_minutes INTEGER,
    -- rating_after_cooking DECIMAL(2,1),
    -- notes TEXT,

    CONSTRAINT fk_user FOREIGN KEY (user_id) REFERENCES auth.users(id) ON DELETE CASCADE,
    CONSTRAINT fk_recipe FOREIGN KEY (recipe_id) REFERENCES recipes(id) ON DELETE CASCADE
);

COMMENT ON TABLE recipe_cooking_events IS
'Event log tracking every time a user cooks a recipe. Enables time-based popularity queries and trend analysis.';

COMMENT ON COLUMN recipe_cooking_events.id IS
'Unique identifier for this cooking event';

COMMENT ON COLUMN recipe_cooking_events.user_id IS
'User who cooked the recipe';

COMMENT ON COLUMN recipe_cooking_events.recipe_id IS
'Recipe that was cooked';

COMMENT ON COLUMN recipe_cooking_events.cooked_at IS
'Timestamp when the recipe was cooked (defaults to NOW())';

COMMENT ON COLUMN recipe_cooking_events.created_at IS
'Timestamp when this event was recorded in the system';

-- ============================================================================
-- INDEXES
-- ============================================================================

-- Index for finding cooking events by recipe and time (most important query pattern)
-- Supports: "Show me all cooking events for recipe X in the last 7 days"
CREATE INDEX idx_cooking_events_recipe_time
ON recipe_cooking_events(recipe_id, cooked_at DESC);

COMMENT ON INDEX idx_cooking_events_recipe_time IS
'Supports time-based queries for recipe cooking events. Enables "most cooked this week" queries.';

-- Index for finding a user's cooking history
-- Supports: "Show me all recipes user X has cooked in the last month"
CREATE INDEX idx_cooking_events_user_time
ON recipe_cooking_events(user_id, cooked_at DESC);

COMMENT ON INDEX idx_cooking_events_user_time IS
'Supports queries for user cooking history over time.';

-- Composite index for trending recipe queries
-- Supports: "Show me recipes with most cooking events in the last 7 days"
CREATE INDEX idx_cooking_events_time_recipe
ON recipe_cooking_events(cooked_at DESC, recipe_id);

COMMENT ON INDEX idx_cooking_events_time_recipe IS
'Supports trending recipe queries by time window. Optimizes aggregation queries.';

-- ============================================================================
-- ROW LEVEL SECURITY (RLS)
-- ============================================================================

-- Enable RLS on the table
ALTER TABLE recipe_cooking_events ENABLE ROW LEVEL SECURITY;

-- Policy: Users can view their own cooking events
CREATE POLICY "Users can view own cooking events"
ON recipe_cooking_events
FOR SELECT
USING (auth.uid() = user_id);

-- Policy: Users can insert their own cooking events
CREATE POLICY "Users can insert own cooking events"
ON recipe_cooking_events
FOR INSERT
WITH CHECK (auth.uid() = user_id);

-- Policy: Users can view cooking events for public recipes (for trending/popular queries)
CREATE POLICY "Users can view cooking events for public recipes"
ON recipe_cooking_events
FOR SELECT
USING (
    EXISTS (
        SELECT 1 FROM recipes
        WHERE recipes.id = recipe_cooking_events.recipe_id
        AND recipes.is_public = true
    )
);

COMMENT ON POLICY "Users can view own cooking events" ON recipe_cooking_events IS
'Users can view their own cooking history';

COMMENT ON POLICY "Users can insert own cooking events" ON recipe_cooking_events IS
'Users can record their own cooking events';

COMMENT ON POLICY "Users can view cooking events for public recipes" ON recipe_cooking_events IS
'Users can view aggregated cooking events for public recipes (enables trending queries)';

-- ============================================================================
-- HELPER FUNCTIONS
-- ============================================================================

-- Function to get trending recipes in a time window
CREATE OR REPLACE FUNCTION get_trending_recipes(
    time_window_days INTEGER DEFAULT 7,
    limit_param INTEGER DEFAULT 20,
    offset_param INTEGER DEFAULT 0
)
RETURNS TABLE (
    recipe_id UUID,
    cook_count BIGINT,
    unique_users BIGINT
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        rce.recipe_id,
        COUNT(*) as cook_count,
        COUNT(DISTINCT rce.user_id) as unique_users
    FROM recipe_cooking_events rce
    INNER JOIN recipes r ON r.id = rce.recipe_id
    WHERE
        rce.cooked_at >= NOW() - INTERVAL '1 day' * time_window_days
        AND r.is_public = true
    GROUP BY rce.recipe_id
    ORDER BY cook_count DESC
    LIMIT limit_param
    OFFSET offset_param;
END;
$$ LANGUAGE plpgsql STABLE;

COMMENT ON FUNCTION get_trending_recipes IS
'Returns recipes ordered by cooking frequency in the specified time window. Includes cook count and unique user count.';

-- Function to get a user's cooking history in a time window
CREATE OR REPLACE FUNCTION get_user_cooking_history(
    user_id_param UUID,
    time_window_days INTEGER DEFAULT 30,
    limit_param INTEGER DEFAULT 20,
    offset_param INTEGER DEFAULT 0
)
RETURNS TABLE (
    recipe_id UUID,
    recipe_title VARCHAR,
    times_cooked BIGINT,
    last_cooked_at TIMESTAMP WITH TIME ZONE,
    first_cooked_at TIMESTAMP WITH TIME ZONE
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        rce.recipe_id,
        r.title,
        COUNT(*) as times_cooked,
        MAX(rce.cooked_at) as last_cooked_at,
        MIN(rce.cooked_at) as first_cooked_at
    FROM recipe_cooking_events rce
    INNER JOIN recipes r ON r.id = rce.recipe_id
    WHERE
        rce.user_id = user_id_param
        AND rce.cooked_at >= NOW() - INTERVAL '1 day' * time_window_days
    GROUP BY rce.recipe_id, r.title
    ORDER BY last_cooked_at DESC
    LIMIT limit_param
    OFFSET offset_param;
END;
$$ LANGUAGE plpgsql STABLE SECURITY DEFINER;

COMMENT ON FUNCTION get_user_cooking_history IS
'Returns a user''s cooking history in the specified time window with aggregated statistics.';

-- ============================================================================
-- DATA BACKFILL (OPTIONAL)
-- ============================================================================

-- Note: We cannot accurately backfill cooking events from existing data because
-- user_recipe_data only stores the LAST cooking timestamp, not every occurrence.
--
-- Options:
-- 1. Start fresh - only track new cooking events going forward
-- 2. Create single events for existing cooked recipes (using last_cooked_at)
--    This gives us partial historical data but loses frequency information
--
-- Uncomment below to backfill with last_cooked_at as a starting point:

-- INSERT INTO recipe_cooking_events (user_id, recipe_id, cooked_at)
-- SELECT
--     user_id,
--     recipe_id,
--     COALESCE(last_cooked_at, created_at) as cooked_at
-- FROM user_recipe_data
-- WHERE times_cooked > 0;

-- ============================================================================
-- VERIFICATION QUERIES
-- ============================================================================

DO $$
BEGIN
    -- Check if table exists
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.tables
        WHERE table_name = 'recipe_cooking_events'
    ) THEN
        RAISE EXCEPTION 'Migration failed: recipe_cooking_events table not created';
    END IF;

    -- Check if indexes exist
    IF NOT EXISTS (
        SELECT 1 FROM pg_indexes
        WHERE tablename = 'recipe_cooking_events' AND indexname = 'idx_cooking_events_recipe_time'
    ) THEN
        RAISE EXCEPTION 'Migration failed: idx_cooking_events_recipe_time index not created';
    END IF;

    -- Check if functions exist
    IF NOT EXISTS (
        SELECT 1 FROM pg_proc WHERE proname = 'get_trending_recipes'
    ) THEN
        RAISE EXCEPTION 'Migration failed: get_trending_recipes function not created';
    END IF;

    RAISE NOTICE 'Migration successful: recipe_cooking_events table, indexes, and functions created';
END $$;

-- Sample queries to test functionality
-- Uncomment to run:

-- -- Get trending recipes in last 7 days
-- SELECT * FROM get_trending_recipes(7, 10, 0);

-- -- Get a user's cooking history in last 30 days
-- SELECT * FROM get_user_cooking_history('user-uuid-here', 30, 10, 0);

-- -- Manual query: Recipes cooked most in last 7 days
-- SELECT
--     r.id,
--     r.title,
--     COUNT(*) as cook_count_last_7_days,
--     COUNT(DISTINCT rce.user_id) as unique_users
-- FROM recipe_cooking_events rce
-- INNER JOIN recipes r ON r.id = rce.recipe_id
-- WHERE rce.cooked_at >= NOW() - INTERVAL '7 days'
-- GROUP BY r.id, r.title
-- ORDER BY cook_count_last_7_days DESC
-- LIMIT 10;
