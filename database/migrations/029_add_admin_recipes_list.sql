-- Migration: 029_add_admin_recipes_list
-- Description: Add PostgreSQL function for admin panel to list recipes with uploader info

-- ============================================================================
-- DROP EXISTING FUNCTION (to allow return type changes)
-- ============================================================================
DROP FUNCTION IF EXISTS public.get_admin_recipes_list(UUID, TEXT, BOOLEAN, INTEGER, INTEGER);

-- ============================================================================
-- FUNCTION: Get admin recipes list
-- Returns paginated list of recipes with uploader info for admin panel
-- ============================================================================
CREATE OR REPLACE FUNCTION public.get_admin_recipes_list(
    p_user_id UUID DEFAULT NULL,        -- Filter by uploader (for user detail page)
    p_search TEXT DEFAULT NULL,         -- Search in title
    p_is_hidden BOOLEAN DEFAULT NULL,   -- Filter by hidden status
    p_limit INTEGER DEFAULT 50,
    p_offset INTEGER DEFAULT 0
)
RETURNS TABLE (
    id UUID,
    title TEXT,
    image_url TEXT,
    source_type TEXT,
    source_url TEXT,
    is_public BOOLEAN,
    is_draft BOOLEAN,
    is_hidden BOOLEAN,
    created_at TIMESTAMPTZ,
    created_by UUID,
    uploader_name TEXT,
    uploader_avatar_url TEXT,
    total_count BIGINT
)
LANGUAGE plpgsql
STABLE
SECURITY DEFINER
AS $$
DECLARE
    v_total BIGINT;
BEGIN
    -- First, get total count for pagination
    SELECT COUNT(*) INTO v_total
    FROM public.recipes r
    WHERE
        (p_user_id IS NULL OR r.created_by = p_user_id)
        AND (p_search IS NULL OR r.title ILIKE '%' || p_search || '%')
        AND (p_is_hidden IS NULL OR r.is_hidden = p_is_hidden);

    -- Return the data with total count
    RETURN QUERY
    SELECT
        r.id,
        r.title::TEXT,
        r.image_url::TEXT,
        r.source_type::TEXT,
        r.source_url::TEXT,
        r.is_public,
        r.is_draft,
        r.is_hidden,
        r.created_at,
        r.created_by,
        public.get_user_display_name(r.created_by) AS uploader_name,
        u.avatar_url::TEXT AS uploader_avatar_url,
        v_total AS total_count
    FROM public.recipes r
    LEFT JOIN public.users u ON u.id = r.created_by
    WHERE
        (p_user_id IS NULL OR r.created_by = p_user_id)
        AND (p_search IS NULL OR r.title ILIKE '%' || p_search || '%')
        AND (p_is_hidden IS NULL OR r.is_hidden = p_is_hidden)
    ORDER BY r.created_at DESC
    LIMIT p_limit
    OFFSET p_offset;
END;
$$;

COMMENT ON FUNCTION public.get_admin_recipes_list IS 'Returns paginated list of recipes with uploader info for admin panel';
