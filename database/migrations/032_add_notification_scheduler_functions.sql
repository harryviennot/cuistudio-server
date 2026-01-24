-- Migration: 032_add_notification_scheduler_functions
-- Description: Add database functions for scheduled notification jobs

-- ============================================================================
-- FUNCTION: Get users eligible for first recipe nudge
-- Users who signed up 24h ago but haven't extracted any recipes
-- ============================================================================
CREATE OR REPLACE FUNCTION public.get_first_recipe_nudge_eligible_users(
    p_window_start TIMESTAMP WITH TIME ZONE,
    p_window_end TIMESTAMP WITH TIME ZONE
)
RETURNS TABLE(id UUID)
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
BEGIN
    RETURN QUERY
    SELECT u.id
    FROM public.users u
    JOIN public.push_tokens pt ON pt.user_id = u.id AND pt.is_active = true
    LEFT JOIN public.notification_preferences np ON np.user_id = u.id
    WHERE
        -- User signed up in the target window (23-25 hours ago)
        u.created_at >= p_window_start
        AND u.created_at <= p_window_end
        -- No recipes extracted
        AND NOT EXISTS (
            SELECT 1 FROM public.recipes r
            WHERE r.user_id = u.id
        )
        -- Notification preferences allow it
        AND COALESCE(np.notifications_enabled, true) = true
        AND COALESCE(np.first_recipe_nudge, true) = true
        -- Haven't already received this notification
        AND NOT EXISTS (
            SELECT 1 FROM public.notification_history nh
            WHERE nh.user_id = u.id
            AND nh.notification_type = 'first_recipe_nudge'
        );
END;
$$;

COMMENT ON FUNCTION public.get_first_recipe_nudge_eligible_users IS 'Get users eligible for first recipe nudge (signed up 24h ago, no recipes)';


-- ============================================================================
-- FUNCTION: Get free tier users for weekly credits notification
-- ============================================================================
CREATE OR REPLACE FUNCTION public.get_weekly_credits_notification_users()
RETURNS TABLE(user_id UUID)
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
BEGIN
    RETURN QUERY
    SELECT DISTINCT pt.user_id
    FROM public.push_tokens pt
    JOIN public.users u ON u.id = pt.user_id
    LEFT JOIN public.notification_preferences np ON np.user_id = pt.user_id
    WHERE
        pt.is_active = true
        -- Free tier users (check subscription status)
        AND COALESCE(u.subscription_tier, 'free') = 'free'
        -- Notification preferences allow it
        AND COALESCE(np.notifications_enabled, true) = true
        AND COALESCE(np.weekly_credits_refresh, true) = true;
END;
$$;

COMMENT ON FUNCTION public.get_weekly_credits_notification_users IS 'Get free tier users eligible for weekly credits refresh notification';


-- ============================================================================
-- FUNCTION: Get users eligible for miss you notification
-- Users inactive for 7+ days
-- ============================================================================
CREATE OR REPLACE FUNCTION public.get_miss_you_eligible_users(
    p_inactive_since TIMESTAMP WITH TIME ZONE
)
RETURNS TABLE(user_id UUID)
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
BEGIN
    RETURN QUERY
    SELECT DISTINCT pt.user_id
    FROM public.push_tokens pt
    LEFT JOIN public.notification_preferences np ON np.user_id = pt.user_id
    LEFT JOIN public.user_activity_stats uas ON uas.user_id = pt.user_id
    WHERE
        pt.is_active = true
        -- Inactive for 7+ days (no app open or last open before cutoff)
        AND (uas.last_app_open_at IS NULL OR uas.last_app_open_at < p_inactive_since)
        -- Notification preferences allow it
        AND COALESCE(np.notifications_enabled, true) = true
        AND COALESCE(np.miss_you, true) = true
        -- Haven't received this notification in the past 7 days
        AND NOT EXISTS (
            SELECT 1 FROM public.notification_history nh
            WHERE nh.user_id = pt.user_id
            AND nh.notification_type = 'miss_you'
            AND nh.sent_at > now() - INTERVAL '7 days'
        );
END;
$$;

COMMENT ON FUNCTION public.get_miss_you_eligible_users IS 'Get users eligible for miss you notification (inactive 7+ days)';


-- ============================================================================
-- FUNCTION: Get users with preference enabled (for bulk notifications)
-- ============================================================================
CREATE OR REPLACE FUNCTION public.get_users_with_preference_enabled(
    p_user_ids UUID[],
    p_preference_name TEXT
)
RETURNS TABLE(user_id UUID)
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
BEGIN
    RETURN QUERY
    SELECT u.id
    FROM unnest(p_user_ids) AS u(id)
    LEFT JOIN public.notification_preferences np ON np.user_id = u.id
    WHERE
        -- Check master toggle
        COALESCE(np.notifications_enabled, true) = true
        -- Check specific preference using dynamic SQL equivalent
        AND CASE p_preference_name
            WHEN 'first_recipe_nudge' THEN COALESCE(np.first_recipe_nudge, true)
            WHEN 'weekly_credits_refresh' THEN COALESCE(np.weekly_credits_refresh, true)
            WHEN 'referral_activated' THEN COALESCE(np.referral_activated, true)
            WHEN 'cook_tonight' THEN COALESCE(np.cook_tonight, true)
            WHEN 'cooking_streak' THEN COALESCE(np.cooking_streak, true)
            WHEN 'miss_you' THEN COALESCE(np.miss_you, true)
            ELSE true
        END = true;
END;
$$;

COMMENT ON FUNCTION public.get_users_with_preference_enabled IS 'Filter user IDs by those who have a specific notification preference enabled';
