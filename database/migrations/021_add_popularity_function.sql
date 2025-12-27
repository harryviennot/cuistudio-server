-- Migration: Add get_popular_recipes function for popularity-based sorting
-- Description: Creates RPC function to get recipes sorted by popularity score
-- Popularity score = (average_rating * rating_count) + total_times_cooked

-- Drop existing function if exists (to handle column changes)
DROP FUNCTION IF EXISTS public.get_popular_recipes(UUID, INTEGER, INTEGER);

-- Create the popularity function
-- Returns all recipe columns plus a calculated popularity_score
CREATE OR REPLACE FUNCTION public.get_popular_recipes(
    category_id_param UUID DEFAULT NULL,
    limit_param INTEGER DEFAULT 20,
    offset_param INTEGER DEFAULT 0
)
RETURNS TABLE (
    id UUID,
    title VARCHAR(200),
    description TEXT,
    image_url TEXT,
    ingredients JSONB,
    instructions JSONB,
    servings INTEGER,
    difficulty VARCHAR(20),
    tags TEXT[],
    prep_time_minutes INTEGER,
    cook_time_minutes INTEGER,
    total_time_minutes INTEGER,
    resting_time_minutes INTEGER,
    source_type VARCHAR(20),
    source_url TEXT,
    created_by UUID,
    original_recipe_id UUID,
    fork_count INTEGER,
    is_public BOOLEAN,
    created_at TIMESTAMPTZ,
    updated_at TIMESTAMPTZ,
    language VARCHAR(2),
    search_vector TSVECTOR,
    average_rating NUMERIC(3,2),
    rating_count INTEGER,
    rating_distribution JSONB,
    total_times_cooked INTEGER,
    is_draft BOOLEAN,
    image_source VARCHAR(50),
    category_id UUID,
    popularity_score NUMERIC
)
LANGUAGE plpgsql
STABLE
AS $$
BEGIN
    RETURN QUERY
    SELECT
        r.id,
        r.title,
        r.description,
        r.image_url,
        r.ingredients,
        r.instructions,
        r.servings,
        r.difficulty,
        r.tags,
        r.prep_time_minutes,
        r.cook_time_minutes,
        r.total_time_minutes,
        r.resting_time_minutes,
        r.source_type,
        r.source_url,
        r.created_by,
        r.original_recipe_id,
        r.fork_count,
        r.is_public,
        r.created_at,
        r.updated_at,
        r.language,
        r.search_vector,
        r.average_rating,
        r.rating_count,
        r.rating_distribution,
        r.total_times_cooked,
        r.is_draft,
        r.image_source,
        r.category_id,
        -- Popularity score: rating quality + engagement
        (COALESCE(r.average_rating, 0) * COALESCE(r.rating_count, 0)) +
        COALESCE(r.total_times_cooked, 0) AS popularity_score
    FROM public.recipes r
    WHERE
        r.is_public = TRUE
        AND r.is_draft = FALSE
        AND (category_id_param IS NULL OR r.category_id = category_id_param)
    ORDER BY
        popularity_score DESC,
        r.created_at DESC
    LIMIT limit_param
    OFFSET offset_param;
END;
$$;

-- Add comment for documentation
COMMENT ON FUNCTION public.get_popular_recipes(UUID, INTEGER, INTEGER) IS
'Returns public recipes sorted by popularity score.
Popularity = (average_rating * rating_count) + total_times_cooked.
Optionally filter by category_id. Results are paginated.';
