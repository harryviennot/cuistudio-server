-- Migration: 027_add_admin_functions
-- Description: Add PostgreSQL functions for admin panel to speed up queries
-- These functions join data from auth.users and public tables efficiently

-- ============================================================================
-- DROP EXISTING FUNCTIONS (to allow return type changes)
-- ============================================================================
DROP FUNCTION IF EXISTS public.get_user_display_name(UUID);
DROP FUNCTION IF EXISTS public.get_admin_users_list(TEXT, BOOLEAN, TEXT, TEXT, TEXT, INTEGER, INTEGER);
DROP FUNCTION IF EXISTS public.get_admin_user_details(UUID);
DROP FUNCTION IF EXISTS public.get_admin_reports_queue(TEXT, TEXT, INTEGER, INTEGER);
DROP FUNCTION IF EXISTS public.get_admin_feedback_queue(TEXT, TEXT, INTEGER, INTEGER);
DROP FUNCTION IF EXISTS public.get_admin_dashboard_stats();
DROP FUNCTION IF EXISTS public.get_user_warnings(UUID);
DROP FUNCTION IF EXISTS public.get_user_moderation_actions(UUID);
DROP FUNCTION IF EXISTS public.get_user_feedback(UUID, INTEGER);

-- ============================================================================
-- HELPER FUNCTION: Get best name for a user
-- Returns the longest non-empty name between auth.users and public.users
-- ============================================================================
CREATE OR REPLACE FUNCTION public.get_user_display_name(
    p_user_id UUID
)
RETURNS TEXT
LANGUAGE plpgsql
STABLE
SECURITY DEFINER
AS $$
DECLARE
    v_auth_name TEXT;
    v_public_name TEXT;
BEGIN
    -- Get name from auth.users (raw_user_meta_data + raw_app_meta_data)
    -- Check multiple possible fields where name might be stored
    SELECT
        COALESCE(
            raw_user_meta_data->>'full_name',
            raw_user_meta_data->>'name',
            raw_user_meta_data->>'display_name',
            raw_user_meta_data->>'preferred_username',
            raw_app_meta_data->>'full_name',
            raw_app_meta_data->>'name'
        )
    INTO v_auth_name
    FROM auth.users
    WHERE id = p_user_id;

    -- Get name from public.users
    SELECT name INTO v_public_name
    FROM public.users
    WHERE id = p_user_id;

    -- Return the longest non-empty name
    IF (v_auth_name IS NULL OR v_auth_name = '') AND (v_public_name IS NULL OR v_public_name = '') THEN
        RETURN NULL;
    ELSIF v_auth_name IS NULL OR v_auth_name = '' THEN
        RETURN v_public_name;
    ELSIF v_public_name IS NULL OR v_public_name = '' THEN
        RETURN v_auth_name;
    ELSIF LENGTH(v_public_name) > LENGTH(v_auth_name) THEN
        RETURN v_public_name;
    ELSE
        RETURN v_auth_name;
    END IF;
END;
$$;

COMMENT ON FUNCTION public.get_user_display_name IS 'Returns the best display name for a user, preferring the longest non-empty name between auth and public tables';

-- ============================================================================
-- FUNCTION: Get admin users list
-- Returns paginated list of users with moderation and subscription info
-- ============================================================================
CREATE OR REPLACE FUNCTION public.get_admin_users_list(
    p_status TEXT DEFAULT NULL,
    p_is_premium BOOLEAN DEFAULT NULL,
    p_search TEXT DEFAULT NULL,
    p_sort_by TEXT DEFAULT 'created_at',
    p_sort_order TEXT DEFAULT 'desc',
    p_limit INTEGER DEFAULT 50,
    p_offset INTEGER DEFAULT 0
)
RETURNS TABLE (
    id UUID,
    name TEXT,
    email TEXT,
    avatar_url TEXT,
    created_at TIMESTAMPTZ,
    last_sign_in_at TIMESTAMPTZ,
    moderation_status TEXT,
    warning_count INTEGER,
    report_count INTEGER,
    reports_submitted BIGINT,
    false_report_count INTEGER,
    reporter_reliability_score NUMERIC,
    is_premium BOOLEAN,
    subscription_expires_at TIMESTAMPTZ,
    is_trial BOOLEAN,
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
    FROM public.users u
    LEFT JOIN public.user_moderation um ON um.user_id = u.id
    LEFT JOIN public.user_subscriptions us ON us.user_id = u.id
    LEFT JOIN auth.users au ON au.id = u.id
    WHERE
        (p_status IS NULL OR COALESCE(um.status, 'good_standing') = p_status)
        AND (p_is_premium IS NULL OR COALESCE(us.is_active, FALSE) = p_is_premium)
        AND (
            p_search IS NULL
            OR u.name ILIKE '%' || p_search || '%'
            OR au.email ILIKE '%' || p_search || '%'
            OR au.raw_user_meta_data->>'full_name' ILIKE '%' || p_search || '%'
        );

    -- Return the data with total count
    RETURN QUERY
    SELECT
        u.id,
        public.get_user_display_name(u.id) AS name,
        au.email::TEXT,
        u.avatar_url,
        u.created_at,
        au.last_sign_in_at,
        COALESCE(um.status, 'good_standing')::TEXT AS moderation_status,
        COALESCE(um.warning_count, 0) AS warning_count,
        COALESCE(um.report_count, 0) AS report_count,
        COALESCE(rs.reports_submitted, 0) AS reports_submitted,
        COALESCE(um.false_report_count, 0) AS false_report_count,
        COALESCE(um.reporter_reliability_score, 100)::NUMERIC / 100.0 AS reporter_reliability_score,
        COALESCE(us.is_active, FALSE) AS is_premium,
        us.expires_at AS subscription_expires_at,
        COALESCE(us.is_trial, FALSE) AS is_trial,
        v_total AS total_count
    FROM public.users u
    LEFT JOIN auth.users au ON au.id = u.id
    LEFT JOIN public.user_moderation um ON um.user_id = u.id
    LEFT JOIN public.user_subscriptions us ON us.user_id = u.id
    LEFT JOIN LATERAL (
        SELECT COUNT(*)::BIGINT AS reports_submitted
        FROM public.content_reports cr
        WHERE cr.reporter_user_id = u.id
    ) rs ON TRUE
    WHERE
        (p_status IS NULL OR COALESCE(um.status, 'good_standing') = p_status)
        AND (p_is_premium IS NULL OR COALESCE(us.is_active, FALSE) = p_is_premium)
        AND (
            p_search IS NULL
            OR u.name ILIKE '%' || p_search || '%'
            OR au.email ILIKE '%' || p_search || '%'
            OR au.raw_user_meta_data->>'full_name' ILIKE '%' || p_search || '%'
        )
    ORDER BY
        CASE WHEN p_sort_by = 'created_at' AND p_sort_order = 'desc' THEN u.created_at END DESC NULLS LAST,
        CASE WHEN p_sort_by = 'created_at' AND p_sort_order = 'asc' THEN u.created_at END ASC NULLS LAST,
        CASE WHEN p_sort_by = 'name' AND p_sort_order = 'desc' THEN public.get_user_display_name(u.id) END DESC NULLS LAST,
        CASE WHEN p_sort_by = 'name' AND p_sort_order = 'asc' THEN public.get_user_display_name(u.id) END ASC NULLS LAST,
        CASE WHEN p_sort_by = 'last_sign_in_at' AND p_sort_order = 'desc' THEN au.last_sign_in_at END DESC NULLS LAST,
        CASE WHEN p_sort_by = 'last_sign_in_at' AND p_sort_order = 'asc' THEN au.last_sign_in_at END ASC NULLS LAST
    LIMIT p_limit
    OFFSET p_offset;
END;
$$;

COMMENT ON FUNCTION public.get_admin_users_list IS 'Returns paginated list of users with moderation and subscription info for admin panel';

-- ============================================================================
-- FUNCTION: Get admin user details
-- Returns complete user details including moderation, warnings, actions, feedback
-- ============================================================================
CREATE OR REPLACE FUNCTION public.get_admin_user_details(
    p_user_id UUID
)
RETURNS TABLE (
    -- User basic info
    user_id UUID,
    user_name TEXT,
    user_avatar_url TEXT,
    email TEXT,
    created_at TIMESTAMPTZ,
    last_sign_in_at TIMESTAMPTZ,
    -- Moderation info
    moderation_id UUID,
    moderation_status TEXT,
    warning_count INTEGER,
    report_count INTEGER,
    false_report_count INTEGER,
    reporter_reliability_score INTEGER,
    suspended_until TIMESTAMPTZ,
    ban_reason TEXT,
    moderation_created_at TIMESTAMPTZ,
    moderation_updated_at TIMESTAMPTZ,
    -- Reporter stats
    reports_submitted BIGINT,
    -- Subscription info
    is_premium BOOLEAN,
    subscription_product_id TEXT,
    subscription_expires_at TIMESTAMPTZ,
    is_trial BOOLEAN
)
LANGUAGE plpgsql
STABLE
SECURITY DEFINER
AS $$
BEGIN
    RETURN QUERY
    SELECT
        u.id AS user_id,
        public.get_user_display_name(u.id) AS user_name,
        u.avatar_url AS user_avatar_url,
        au.email::TEXT,
        u.created_at,
        au.last_sign_in_at,
        -- Moderation
        um.id AS moderation_id,
        COALESCE(um.status, 'good_standing')::TEXT AS moderation_status,
        COALESCE(um.warning_count, 0) AS warning_count,
        COALESCE(um.report_count, 0) AS report_count,
        COALESCE(um.false_report_count, 0) AS false_report_count,
        COALESCE(um.reporter_reliability_score, 100) AS reporter_reliability_score,
        um.suspended_until,
        um.ban_reason,
        um.created_at AS moderation_created_at,
        um.updated_at AS moderation_updated_at,
        -- Reports submitted
        COALESCE(rs.cnt, 0) AS reports_submitted,
        -- Subscription
        COALESCE(us.is_active, FALSE) AS is_premium,
        us.product_id AS subscription_product_id,
        us.expires_at AS subscription_expires_at,
        COALESCE(us.is_trial, FALSE) AS is_trial
    FROM public.users u
    LEFT JOIN auth.users au ON au.id = u.id
    LEFT JOIN public.user_moderation um ON um.user_id = u.id
    LEFT JOIN public.user_subscriptions us ON us.user_id = u.id
    LEFT JOIN LATERAL (
        SELECT COUNT(*)::BIGINT AS cnt
        FROM public.content_reports cr
        WHERE cr.reporter_user_id = u.id
    ) rs ON TRUE
    WHERE u.id = p_user_id;
END;
$$;

COMMENT ON FUNCTION public.get_admin_user_details IS 'Returns complete user details for admin user detail page';

-- ============================================================================
-- FUNCTION: Get admin reports queue
-- Returns paginated list of content reports with recipe and reporter info
-- ============================================================================
CREATE OR REPLACE FUNCTION public.get_admin_reports_queue(
    p_status TEXT DEFAULT NULL,
    p_reason TEXT DEFAULT NULL,
    p_limit INTEGER DEFAULT 50,
    p_offset INTEGER DEFAULT 0
)
RETURNS TABLE (
    -- Report info
    id UUID,
    recipe_id UUID,
    reporter_user_id UUID,
    reason TEXT,
    description TEXT,
    status TEXT,
    priority INTEGER,
    created_at TIMESTAMPTZ,
    updated_at TIMESTAMPTZ,
    resolved_by UUID,
    resolved_at TIMESTAMPTZ,
    resolution_notes TEXT,
    -- Recipe info
    recipe_title TEXT,
    recipe_image_url TEXT,
    recipe_source_type TEXT,
    recipe_created_by UUID,
    recipe_is_hidden BOOLEAN,
    -- Reporter info
    reporter_name TEXT,
    reporter_avatar_url TEXT,
    reporter_reliability_score INTEGER,
    -- Recipe owner info
    recipe_owner_name TEXT,
    recipe_owner_avatar_url TEXT,
    -- Total count
    total_count BIGINT
)
LANGUAGE plpgsql
STABLE
SECURITY DEFINER
AS $$
DECLARE
    v_total BIGINT;
BEGIN
    -- Get total count
    SELECT COUNT(*) INTO v_total
    FROM public.content_reports cr
    WHERE
        (p_status IS NULL OR cr.status = p_status)
        AND (p_reason IS NULL OR cr.reason = p_reason);

    RETURN QUERY
    SELECT
        cr.id,
        cr.recipe_id,
        cr.reporter_user_id,
        cr.reason::TEXT,
        cr.description,
        cr.status::TEXT,
        cr.priority,
        cr.created_at,
        cr.updated_at,
        cr.resolved_by,
        cr.resolved_at,
        cr.resolution_notes,
        -- Recipe
        r.title::TEXT AS recipe_title,
        r.image_url AS recipe_image_url,
        r.source_type::TEXT AS recipe_source_type,
        r.created_by AS recipe_created_by,
        COALESCE(r.is_hidden, FALSE) AS recipe_is_hidden,
        -- Reporter
        public.get_user_display_name(cr.reporter_user_id) AS reporter_name,
        reporter_u.avatar_url AS reporter_avatar_url,
        COALESCE(reporter_um.reporter_reliability_score, 100) AS reporter_reliability_score,
        -- Recipe owner
        public.get_user_display_name(r.created_by) AS recipe_owner_name,
        owner_u.avatar_url AS recipe_owner_avatar_url,
        v_total AS total_count
    FROM public.content_reports cr
    LEFT JOIN public.recipes r ON r.id = cr.recipe_id
    LEFT JOIN public.users reporter_u ON reporter_u.id = cr.reporter_user_id
    LEFT JOIN public.user_moderation reporter_um ON reporter_um.user_id = cr.reporter_user_id
    LEFT JOIN public.users owner_u ON owner_u.id = r.created_by
    WHERE
        (p_status IS NULL OR cr.status = p_status)
        AND (p_reason IS NULL OR cr.reason = p_reason)
    ORDER BY
        CASE WHEN cr.status = 'pending' THEN 0 WHEN cr.status = 'in_review' THEN 1 ELSE 2 END,
        cr.priority DESC,
        cr.created_at DESC
    LIMIT p_limit
    OFFSET p_offset;
END;
$$;

COMMENT ON FUNCTION public.get_admin_reports_queue IS 'Returns paginated content reports queue for admin panel';

-- ============================================================================
-- FUNCTION: Get admin feedback queue
-- Returns paginated list of extraction feedback with recipe and user info
-- ============================================================================
CREATE OR REPLACE FUNCTION public.get_admin_feedback_queue(
    p_status TEXT DEFAULT NULL,
    p_category TEXT DEFAULT NULL,
    p_limit INTEGER DEFAULT 50,
    p_offset INTEGER DEFAULT 0
)
RETURNS TABLE (
    -- Feedback info
    id UUID,
    recipe_id UUID,
    user_id UUID,
    category TEXT,
    description TEXT,
    status TEXT,
    created_at TIMESTAMPTZ,
    updated_at TIMESTAMPTZ,
    resolved_by UUID,
    resolved_at TIMESTAMPTZ,
    resolution_notes TEXT,
    was_helpful BOOLEAN,
    extraction_job_id UUID,
    -- Recipe info
    recipe_title TEXT,
    recipe_image_url TEXT,
    recipe_source_type TEXT,
    recipe_source_url TEXT,
    -- User info
    user_name TEXT,
    user_avatar_url TEXT,
    -- Total count
    total_count BIGINT
)
LANGUAGE plpgsql
STABLE
SECURITY DEFINER
AS $$
DECLARE
    v_total BIGINT;
BEGIN
    -- Get total count
    SELECT COUNT(*) INTO v_total
    FROM public.extraction_feedback ef
    WHERE
        (p_status IS NULL OR ef.status = p_status)
        AND (p_category IS NULL OR ef.category = p_category);

    RETURN QUERY
    SELECT
        ef.id,
        ef.recipe_id,
        ef.user_id,
        ef.category::TEXT,
        ef.description,
        ef.status::TEXT,
        ef.created_at,
        ef.updated_at,
        ef.resolved_by,
        ef.resolved_at,
        ef.resolution_notes,
        ef.was_helpful,
        ef.extraction_job_id,
        -- Recipe
        r.title::TEXT AS recipe_title,
        r.image_url AS recipe_image_url,
        r.source_type::TEXT AS recipe_source_type,
        r.source_url AS recipe_source_url,
        -- User
        public.get_user_display_name(ef.user_id) AS user_name,
        u.avatar_url AS user_avatar_url,
        v_total AS total_count
    FROM public.extraction_feedback ef
    LEFT JOIN public.recipes r ON r.id = ef.recipe_id
    LEFT JOIN public.users u ON u.id = ef.user_id
    WHERE
        (p_status IS NULL OR ef.status = p_status)
        AND (p_category IS NULL OR ef.category = p_category)
    ORDER BY
        CASE WHEN ef.status = 'pending' THEN 0 WHEN ef.status = 'in_review' THEN 1 ELSE 2 END,
        ef.created_at DESC
    LIMIT p_limit
    OFFSET p_offset;
END;
$$;

COMMENT ON FUNCTION public.get_admin_feedback_queue IS 'Returns paginated extraction feedback queue for admin panel';

-- ============================================================================
-- FUNCTION: Get admin dashboard stats
-- Returns aggregated statistics for the admin dashboard
-- ============================================================================
CREATE OR REPLACE FUNCTION public.get_admin_dashboard_stats()
RETURNS TABLE (
    -- Report stats
    reports_pending BIGINT,
    reports_in_review BIGINT,
    reports_resolved_today BIGINT,
    reports_resolved_week BIGINT,
    reports_by_reason JSONB,
    -- Feedback stats
    feedback_pending BIGINT,
    feedback_in_review BIGINT,
    feedback_resolved_today BIGINT,
    feedback_resolved_week BIGINT,
    feedback_helpful_count BIGINT,
    feedback_by_category JSONB,
    -- User stats
    users_total BIGINT,
    users_warned BIGINT,
    users_suspended BIGINT,
    users_banned BIGINT,
    users_premium BIGINT,
    users_new_today BIGINT,
    users_new_week BIGINT,
    -- Action stats
    actions_today BIGINT,
    actions_week BIGINT
)
LANGUAGE plpgsql
STABLE
SECURITY DEFINER
AS $$
BEGIN
    RETURN QUERY
    SELECT
        -- Report stats
        (SELECT COUNT(*) FROM public.content_reports WHERE status = 'pending')::BIGINT AS reports_pending,
        (SELECT COUNT(*) FROM public.content_reports WHERE status = 'in_review')::BIGINT AS reports_in_review,
        (SELECT COUNT(*) FROM public.content_reports WHERE status = 'resolved' AND resolved_at >= CURRENT_DATE)::BIGINT AS reports_resolved_today,
        (SELECT COUNT(*) FROM public.content_reports WHERE status = 'resolved' AND resolved_at >= CURRENT_DATE - INTERVAL '7 days')::BIGINT AS reports_resolved_week,
        (SELECT COALESCE(jsonb_object_agg(reason, cnt), '{}'::jsonb) FROM (
            SELECT reason, COUNT(*) as cnt FROM public.content_reports WHERE status = 'pending' GROUP BY reason
        ) r)::JSONB AS reports_by_reason,
        -- Feedback stats
        (SELECT COUNT(*) FROM public.extraction_feedback WHERE status = 'pending')::BIGINT AS feedback_pending,
        (SELECT COUNT(*) FROM public.extraction_feedback WHERE status = 'in_review')::BIGINT AS feedback_in_review,
        (SELECT COUNT(*) FROM public.extraction_feedback WHERE status = 'resolved' AND resolved_at >= CURRENT_DATE)::BIGINT AS feedback_resolved_today,
        (SELECT COUNT(*) FROM public.extraction_feedback WHERE status = 'resolved' AND resolved_at >= CURRENT_DATE - INTERVAL '7 days')::BIGINT AS feedback_resolved_week,
        (SELECT COUNT(*) FROM public.extraction_feedback WHERE was_helpful = true)::BIGINT AS feedback_helpful_count,
        (SELECT COALESCE(jsonb_object_agg(category, cnt), '{}'::jsonb) FROM (
            SELECT category, COUNT(*) as cnt FROM public.extraction_feedback WHERE status = 'pending' GROUP BY category
        ) f)::JSONB AS feedback_by_category,
        -- User stats
        (SELECT COUNT(*) FROM public.users)::BIGINT AS users_total,
        (SELECT COUNT(*) FROM public.user_moderation WHERE status = 'warned')::BIGINT AS users_warned,
        (SELECT COUNT(*) FROM public.user_moderation WHERE status = 'suspended')::BIGINT AS users_suspended,
        (SELECT COUNT(*) FROM public.user_moderation WHERE status = 'banned')::BIGINT AS users_banned,
        (SELECT COUNT(*) FROM public.user_subscriptions WHERE is_active = true)::BIGINT AS users_premium,
        (SELECT COUNT(*) FROM public.users WHERE created_at >= CURRENT_DATE)::BIGINT AS users_new_today,
        (SELECT COUNT(*) FROM public.users WHERE created_at >= CURRENT_DATE - INTERVAL '7 days')::BIGINT AS users_new_week,
        -- Action stats
        (SELECT COUNT(*) FROM public.moderation_actions WHERE created_at >= CURRENT_DATE)::BIGINT AS actions_today,
        (SELECT COUNT(*) FROM public.moderation_actions WHERE created_at >= CURRENT_DATE - INTERVAL '7 days')::BIGINT AS actions_week;
END;
$$;

COMMENT ON FUNCTION public.get_admin_dashboard_stats IS 'Returns aggregated statistics for the admin dashboard';

-- ============================================================================
-- FUNCTION: Get user warnings list
-- Returns list of warnings for a specific user
-- ============================================================================
CREATE OR REPLACE FUNCTION public.get_user_warnings(
    p_user_id UUID
)
RETURNS TABLE (
    id UUID,
    reason TEXT,
    content_report_id UUID,
    recipe_id UUID,
    acknowledged_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ,
    -- Issuer info
    issuer_id UUID,
    issuer_name TEXT,
    issuer_avatar_url TEXT,
    -- Recipe info (if related)
    recipe_title TEXT,
    recipe_image_url TEXT
)
LANGUAGE plpgsql
STABLE
SECURITY DEFINER
AS $$
BEGIN
    RETURN QUERY
    SELECT
        w.id,
        w.reason,
        w.content_report_id,
        w.recipe_id,
        w.acknowledged_at,
        w.created_at,
        -- Issuer
        w.issued_by AS issuer_id,
        public.get_user_display_name(w.issued_by) AS issuer_name,
        issuer_u.avatar_url AS issuer_avatar_url,
        -- Recipe
        r.title::TEXT AS recipe_title,
        r.image_url AS recipe_image_url
    FROM public.user_warnings w
    LEFT JOIN public.users issuer_u ON issuer_u.id = w.issued_by
    LEFT JOIN public.recipes r ON r.id = w.recipe_id
    WHERE w.user_id = p_user_id
    ORDER BY w.created_at DESC;
END;
$$;

COMMENT ON FUNCTION public.get_user_warnings IS 'Returns list of warnings for a specific user';

-- ============================================================================
-- FUNCTION: Get user moderation actions
-- Returns list of moderation actions targeting a specific user
-- ============================================================================
CREATE OR REPLACE FUNCTION public.get_user_moderation_actions(
    p_user_id UUID
)
RETURNS TABLE (
    id UUID,
    action_type TEXT,
    reason TEXT,
    notes TEXT,
    duration_days INTEGER,
    created_at TIMESTAMPTZ,
    -- Moderator info
    moderator_id UUID,
    moderator_name TEXT,
    moderator_avatar_url TEXT,
    -- Target recipe info (if applicable)
    target_recipe_id UUID,
    target_recipe_title TEXT,
    target_recipe_image_url TEXT
)
LANGUAGE plpgsql
STABLE
SECURITY DEFINER
AS $$
BEGIN
    RETURN QUERY
    SELECT
        ma.id,
        ma.action_type::TEXT,
        ma.reason,
        ma.notes,
        ma.duration_days,
        ma.created_at,
        -- Moderator
        ma.moderator_id,
        public.get_user_display_name(ma.moderator_id) AS moderator_name,
        mod_u.avatar_url AS moderator_avatar_url,
        -- Target recipe
        ma.target_recipe_id,
        r.title::TEXT AS target_recipe_title,
        r.image_url AS target_recipe_image_url
    FROM public.moderation_actions ma
    LEFT JOIN public.users mod_u ON mod_u.id = ma.moderator_id
    LEFT JOIN public.recipes r ON r.id = ma.target_recipe_id
    WHERE ma.target_user_id = p_user_id
    ORDER BY ma.created_at DESC;
END;
$$;

COMMENT ON FUNCTION public.get_user_moderation_actions IS 'Returns list of moderation actions targeting a specific user';

-- ============================================================================
-- FUNCTION: Get user extraction feedback
-- Returns list of extraction feedback submitted by a specific user
-- ============================================================================
CREATE OR REPLACE FUNCTION public.get_user_feedback(
    p_user_id UUID,
    p_limit INTEGER DEFAULT 20
)
RETURNS TABLE (
    id UUID,
    recipe_id UUID,
    category TEXT,
    description TEXT,
    status TEXT,
    created_at TIMESTAMPTZ,
    resolved_at TIMESTAMPTZ,
    was_helpful BOOLEAN,
    -- Recipe info
    recipe_title TEXT,
    recipe_image_url TEXT
)
LANGUAGE plpgsql
STABLE
SECURITY DEFINER
AS $$
BEGIN
    RETURN QUERY
    SELECT
        ef.id,
        ef.recipe_id,
        ef.category::TEXT,
        ef.description,
        ef.status::TEXT,
        ef.created_at,
        ef.resolved_at,
        ef.was_helpful,
        -- Recipe
        r.title::TEXT AS recipe_title,
        r.image_url AS recipe_image_url
    FROM public.extraction_feedback ef
    LEFT JOIN public.recipes r ON r.id = ef.recipe_id
    WHERE ef.user_id = p_user_id
    ORDER BY ef.created_at DESC
    LIMIT p_limit;
END;
$$;

COMMENT ON FUNCTION public.get_user_feedback IS 'Returns list of extraction feedback submitted by a specific user';

-- ============================================================================
-- GRANT EXECUTE PERMISSIONS
-- Only authenticated users with admin role should call these via RPC
-- The SECURITY DEFINER allows them to access auth.users
-- ============================================================================
-- Note: These functions use SECURITY DEFINER to access auth.users
-- Access control should be enforced at the application level (admin check)
