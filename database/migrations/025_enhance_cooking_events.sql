-- Migration: Enhance recipe cooking events with rating, image, and duration
-- Created: 2025-12-05
-- Description: Adds rating, image_url, and duration_minutes columns to recipe_cooking_events
--              to create a comprehensive cooking journal experience.
--
-- Changes:
-- 1. Add rating column - stores the rating given at this specific cooking session
-- 2. Add image_url column - stores a photo taken during this cooking session
-- 3. Add duration_minutes column - stores actual cooking time for this session
-- 4. Update get_user_cooking_history function to return individual events with new fields

-- ============================================================================
-- SCHEMA CHANGES
-- ============================================================================

-- Add new columns to recipe_cooking_events
ALTER TABLE recipe_cooking_events
ADD COLUMN IF NOT EXISTS rating DECIMAL(2,1) CHECK (rating IS NULL OR (rating >= 0.5 AND rating <= 5.0)),
ADD COLUMN IF NOT EXISTS image_url TEXT,
ADD COLUMN IF NOT EXISTS duration_minutes INTEGER CHECK (duration_minutes IS NULL OR duration_minutes >= 0);

COMMENT ON COLUMN recipe_cooking_events.rating IS
'Rating given at this specific cooking session (0.5-5.0). May differ from user_recipe_data.rating which is the current/latest rating.';

COMMENT ON COLUMN recipe_cooking_events.image_url IS
'URL to a photo taken during this cooking session, stored in cooking-events bucket.';

COMMENT ON COLUMN recipe_cooking_events.duration_minutes IS
'Actual cooking duration in minutes for this session, tracked by the app timer.';

-- ============================================================================
-- UPDATE FUNCTION: get_user_cooking_history
-- ============================================================================

-- Drop the existing function first (signature is changing)
DROP FUNCTION IF EXISTS get_user_cooking_history(UUID, INTEGER, INTEGER, INTEGER);

-- Create new version that returns individual cooking events (not aggregated)
CREATE OR REPLACE FUNCTION get_user_cooking_history(
    user_id_param UUID,
    time_window_days INTEGER DEFAULT 365,
    limit_param INTEGER DEFAULT 20,
    offset_param INTEGER DEFAULT 0
)
RETURNS TABLE (
    event_id UUID,
    recipe_id UUID,
    recipe_title VARCHAR,
    recipe_image_url TEXT,
    difficulty VARCHAR,
    rating DECIMAL(2,1),
    cooking_image_url TEXT,
    duration_minutes INTEGER,
    cooked_at TIMESTAMP WITH TIME ZONE,
    times_cooked BIGINT
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        rce.id as event_id,
        rce.recipe_id,
        r.title as recipe_title,
        r.image_url as recipe_image_url,
        r.difficulty,
        rce.rating,
        rce.image_url as cooking_image_url,
        rce.duration_minutes,
        rce.cooked_at,
        (
            SELECT COUNT(*)
            FROM recipe_cooking_events rce2
            WHERE rce2.recipe_id = rce.recipe_id
            AND rce2.user_id = user_id_param
        ) as times_cooked
    FROM recipe_cooking_events rce
    INNER JOIN recipes r ON r.id = rce.recipe_id
    WHERE
        rce.user_id = user_id_param
        AND rce.cooked_at >= NOW() - INTERVAL '1 day' * time_window_days
    ORDER BY rce.cooked_at DESC
    LIMIT limit_param
    OFFSET offset_param;
END;
$$ LANGUAGE plpgsql STABLE SECURITY DEFINER;

COMMENT ON FUNCTION get_user_cooking_history IS
'Returns individual cooking events for a user with recipe details and per-event data (rating, photo, duration). Each row is a single cooking session.';

-- ============================================================================
-- VERIFICATION
-- ============================================================================

DO $$
BEGIN
    -- Check if columns exist
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'recipe_cooking_events' AND column_name = 'rating'
    ) THEN
        RAISE EXCEPTION 'Migration failed: rating column not created';
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'recipe_cooking_events' AND column_name = 'image_url'
    ) THEN
        RAISE EXCEPTION 'Migration failed: image_url column not created';
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'recipe_cooking_events' AND column_name = 'duration_minutes'
    ) THEN
        RAISE EXCEPTION 'Migration failed: duration_minutes column not created';
    END IF;

    RAISE NOTICE 'Migration successful: recipe_cooking_events enhanced with rating, image_url, and duration_minutes columns';
END $$;
