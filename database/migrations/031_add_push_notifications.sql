-- Migration: 031_add_push_notifications
-- Description: Add tables for push notifications, user preferences, and activity tracking
-- This enables server-driven push notifications via Expo Push API

-- ============================================================================
-- AUTH STUB FOR CI/CD TESTING
-- Creates auth schema and uid() function ONLY if they don't exist.
-- Safe for production Supabase - does nothing if auth.uid() already exists.
-- ============================================================================
CREATE SCHEMA IF NOT EXISTS auth;

DO $$
BEGIN
  -- Only create auth.uid() if it doesn't already exist
  IF NOT EXISTS (
    SELECT 1 FROM pg_proc p
    JOIN pg_namespace n ON p.pronamespace = n.oid
    WHERE n.nspname = 'auth' AND p.proname = 'uid'
  ) THEN
    CREATE FUNCTION auth.uid()
    RETURNS uuid
    LANGUAGE sql
    STABLE
    AS $func$
      SELECT COALESCE(
        nullif(current_setting('request.jwt.claim.sub', true), ''),
        (nullif(current_setting('request.jwt.claims', true), '')::jsonb ->> 'sub')
      )::uuid
    $func$;
  END IF;
END
$$;

-- ============================================================================
-- PUSH TOKENS (device registration for push notifications)
-- ============================================================================
CREATE TABLE IF NOT EXISTS public.push_tokens (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,
    expo_push_token TEXT NOT NULL,            -- "ExponentPushToken[xxxx]"
    platform TEXT NOT NULL,                   -- 'ios' or 'android'
    device_id TEXT,                           -- Optional device identifier
    app_version TEXT,                         -- App version for compatibility tracking
    is_active BOOLEAN DEFAULT true,           -- Soft delete for invalid tokens
    last_used_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
    UNIQUE(expo_push_token)
);

COMMENT ON TABLE public.push_tokens IS 'Device push notification tokens for Expo Push API';
COMMENT ON COLUMN public.push_tokens.expo_push_token IS 'Expo push token in format ExponentPushToken[xxxx]';
COMMENT ON COLUMN public.push_tokens.platform IS 'Device platform: ios or android';
COMMENT ON COLUMN public.push_tokens.is_active IS 'False if token is known to be invalid (device unregistered)';

-- ============================================================================
-- NOTIFICATION PREFERENCES (user opt-out settings)
-- ============================================================================
CREATE TABLE IF NOT EXISTS public.notification_preferences (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,
    notifications_enabled BOOLEAN DEFAULT true,   -- Master toggle
    first_recipe_nudge BOOLEAN DEFAULT true,      -- 24h after signup nudge
    weekly_credits_refresh BOOLEAN DEFAULT true,  -- Monday credits reset
    referral_activated BOOLEAN DEFAULT true,      -- When someone uses your code
    cook_tonight BOOLEAN DEFAULT true,            -- Evening recipe suggestions
    cooking_streak BOOLEAN DEFAULT true,          -- Streak celebrations
    miss_you BOOLEAN DEFAULT true,                -- Re-engagement after 7 days
    timezone TEXT DEFAULT 'UTC',                  -- User's timezone for timing
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
    UNIQUE(user_id)
);

COMMENT ON TABLE public.notification_preferences IS 'User notification preferences and opt-out settings';
COMMENT ON COLUMN public.notification_preferences.notifications_enabled IS 'Master toggle - if false, no notifications sent';
COMMENT ON COLUMN public.notification_preferences.timezone IS 'User timezone for notification timing calculations';

-- ============================================================================
-- NOTIFICATION HISTORY (sent notifications log for analytics & deduplication)
-- ============================================================================
CREATE TABLE IF NOT EXISTS public.notification_history (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,
    notification_type TEXT NOT NULL,              -- Type enum value
    title TEXT NOT NULL,
    body TEXT NOT NULL,
    data JSONB DEFAULT '{}',                      -- Deep link data, recipe_id, etc.
    expo_ticket_id TEXT,                          -- Expo Push API ticket ID
    status TEXT DEFAULT 'sent',                   -- 'sent', 'delivered', 'failed'
    error_message TEXT,                           -- Error details if failed
    sent_at TIMESTAMP WITH TIME ZONE DEFAULT now()
);

COMMENT ON TABLE public.notification_history IS 'Log of all sent push notifications';
COMMENT ON COLUMN public.notification_history.notification_type IS 'Type: first_recipe_nudge, weekly_credits_refresh, referral_activated, cook_tonight, cooking_streak, miss_you';
COMMENT ON COLUMN public.notification_history.data IS 'JSONB payload for deep linking (screen, recipe_id, etc.)';
COMMENT ON COLUMN public.notification_history.expo_ticket_id IS 'Expo Push API ticket ID for delivery tracking';

-- ============================================================================
-- USER ACTIVITY STATS (for smart timing algorithm & streak tracking)
-- ============================================================================
CREATE TABLE IF NOT EXISTS public.user_activity_stats (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,
    -- App usage tracking for smart notification timing
    app_opens_by_hour JSONB DEFAULT '{}',         -- {"17": 45, "18": 32} - opens per hour
    total_app_opens INTEGER DEFAULT 0,
    preferred_notification_hour INTEGER,          -- Computed: most frequent hour
    last_app_open_at TIMESTAMP WITH TIME ZONE,
    -- Cooking streak tracking
    current_cooking_streak INTEGER DEFAULT 0,
    longest_cooking_streak INTEGER DEFAULT 0,
    last_cook_date DATE,
    -- Notification frequency tracking
    last_cook_tonight_sent_at TIMESTAMP WITH TIME ZONE,  -- For weekly frequency when inactive
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
    UNIQUE(user_id)
);

COMMENT ON TABLE public.user_activity_stats IS 'User activity tracking for smart notification timing and cooking streaks';
COMMENT ON COLUMN public.user_activity_stats.app_opens_by_hour IS 'JSON object tracking app opens by hour (0-23) for smart timing';
COMMENT ON COLUMN public.user_activity_stats.preferred_notification_hour IS 'Computed optimal hour for notifications based on usage patterns';
COMMENT ON COLUMN public.user_activity_stats.current_cooking_streak IS 'Current consecutive days cooking';
COMMENT ON COLUMN public.user_activity_stats.last_cook_tonight_sent_at IS 'Last cook tonight notification sent - for weekly frequency when inactive';

-- ============================================================================
-- INDEXES
-- ============================================================================
CREATE INDEX IF NOT EXISTS idx_push_tokens_user_id ON public.push_tokens(user_id);
CREATE INDEX IF NOT EXISTS idx_push_tokens_active ON public.push_tokens(is_active) WHERE is_active = true;
CREATE INDEX IF NOT EXISTS idx_push_tokens_expo ON public.push_tokens(expo_push_token);

CREATE INDEX IF NOT EXISTS idx_notification_preferences_user_id ON public.notification_preferences(user_id);

CREATE INDEX IF NOT EXISTS idx_notification_history_user_id ON public.notification_history(user_id);
CREATE INDEX IF NOT EXISTS idx_notification_history_type ON public.notification_history(notification_type);
CREATE INDEX IF NOT EXISTS idx_notification_history_sent_at ON public.notification_history(sent_at);

CREATE INDEX IF NOT EXISTS idx_user_activity_stats_user_id ON public.user_activity_stats(user_id);
CREATE INDEX IF NOT EXISTS idx_user_activity_stats_last_app_open ON public.user_activity_stats(last_app_open_at);
CREATE INDEX IF NOT EXISTS idx_user_activity_stats_preferred_hour ON public.user_activity_stats(preferred_notification_hour);

-- ============================================================================
-- ROW LEVEL SECURITY
-- ============================================================================
ALTER TABLE public.push_tokens ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.notification_preferences ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.notification_history ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.user_activity_stats ENABLE ROW LEVEL SECURITY;

-- Users can view and manage their own push tokens
CREATE POLICY "Users can view own push tokens"
    ON public.push_tokens FOR SELECT
    USING (auth.uid() = user_id);

CREATE POLICY "Users can insert own push tokens"
    ON public.push_tokens FOR INSERT
    WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update own push tokens"
    ON public.push_tokens FOR UPDATE
    USING (auth.uid() = user_id);

CREATE POLICY "Users can delete own push tokens"
    ON public.push_tokens FOR DELETE
    USING (auth.uid() = user_id);

-- Users can view and update their own notification preferences
CREATE POLICY "Users can view own notification preferences"
    ON public.notification_preferences FOR SELECT
    USING (auth.uid() = user_id);

CREATE POLICY "Users can insert own notification preferences"
    ON public.notification_preferences FOR INSERT
    WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update own notification preferences"
    ON public.notification_preferences FOR UPDATE
    USING (auth.uid() = user_id);

-- Users can view their own notification history
CREATE POLICY "Users can view own notification history"
    ON public.notification_history FOR SELECT
    USING (auth.uid() = user_id);

-- Users can view and update their own activity stats
CREATE POLICY "Users can view own activity stats"
    ON public.user_activity_stats FOR SELECT
    USING (auth.uid() = user_id);

CREATE POLICY "Users can insert own activity stats"
    ON public.user_activity_stats FOR INSERT
    WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update own activity stats"
    ON public.user_activity_stats FOR UPDATE
    USING (auth.uid() = user_id);

-- ============================================================================
-- FUNCTIONS
-- ============================================================================

-- Function to track app open and update smart timing algorithm
CREATE OR REPLACE FUNCTION public.track_app_open(p_user_id UUID, p_hour INTEGER)
RETURNS void
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
DECLARE
    v_stats user_activity_stats;
    v_max_hour INTEGER;
    v_max_count INTEGER;
BEGIN
    -- Upsert stats record
    INSERT INTO public.user_activity_stats (user_id, last_app_open_at)
    VALUES (p_user_id, now())
    ON CONFLICT (user_id) DO UPDATE SET
        app_opens_by_hour = COALESCE(user_activity_stats.app_opens_by_hour, '{}'::jsonb) ||
            jsonb_build_object(
                p_hour::text,
                COALESCE((user_activity_stats.app_opens_by_hour->>p_hour::text)::integer, 0) + 1
            ),
        total_app_opens = user_activity_stats.total_app_opens + 1,
        last_app_open_at = now(),
        updated_at = now()
    RETURNING * INTO v_stats;

    -- Recalculate preferred notification hour if we have enough data (5+ opens)
    IF v_stats.total_app_opens >= 5 THEN
        SELECT key::integer, value::integer
        INTO v_max_hour, v_max_count
        FROM jsonb_each_text(v_stats.app_opens_by_hour)
        ORDER BY value::integer DESC
        LIMIT 1;

        -- Update preferred hour
        UPDATE public.user_activity_stats
        SET preferred_notification_hour = v_max_hour
        WHERE user_id = p_user_id;
    END IF;
END;
$$;

COMMENT ON FUNCTION public.track_app_open IS 'Track app open event and update smart timing algorithm. Call with current UTC hour (0-23).';

-- Function to update cooking streak
CREATE OR REPLACE FUNCTION public.update_cooking_streak(p_user_id UUID)
RETURNS TABLE(
    current_streak INTEGER,
    longest_streak INTEGER,
    is_milestone BOOLEAN,
    milestone_days INTEGER
)
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
DECLARE
    v_last_cook_date DATE;
    v_current_streak INTEGER;
    v_longest_streak INTEGER;
    v_today DATE := CURRENT_DATE;
    v_is_milestone BOOLEAN := false;
    v_milestone_days INTEGER := 0;
BEGIN
    -- Get current stats
    SELECT uas.last_cook_date, uas.current_cooking_streak, uas.longest_cooking_streak
    INTO v_last_cook_date, v_current_streak, v_longest_streak
    FROM public.user_activity_stats uas
    WHERE uas.user_id = p_user_id;

    -- Initialize if no record exists
    IF v_current_streak IS NULL THEN
        INSERT INTO public.user_activity_stats (user_id, current_cooking_streak, longest_cooking_streak, last_cook_date)
        VALUES (p_user_id, 1, 1, v_today)
        ON CONFLICT (user_id) DO UPDATE SET
            current_cooking_streak = 1,
            longest_cooking_streak = GREATEST(user_activity_stats.longest_cooking_streak, 1),
            last_cook_date = v_today,
            updated_at = now();

        current_streak := 1;
        longest_streak := 1;
        is_milestone := false;
        milestone_days := 0;
        RETURN NEXT;
        RETURN;
    END IF;

    -- Calculate new streak
    IF v_last_cook_date = v_today THEN
        -- Already cooked today, no change
        current_streak := v_current_streak;
        longest_streak := v_longest_streak;
    ELSIF v_last_cook_date = v_today - 1 THEN
        -- Consecutive day - increment streak
        v_current_streak := v_current_streak + 1;
        v_longest_streak := GREATEST(v_longest_streak, v_current_streak);

        -- Check for milestone (3, 7, 14, 30 days)
        IF v_current_streak IN (3, 7, 14, 30) THEN
            v_is_milestone := true;
            v_milestone_days := v_current_streak;
        END IF;

        -- Update database
        UPDATE public.user_activity_stats
        SET current_cooking_streak = v_current_streak,
            longest_cooking_streak = v_longest_streak,
            last_cook_date = v_today,
            updated_at = now()
        WHERE user_id = p_user_id;

        current_streak := v_current_streak;
        longest_streak := v_longest_streak;
    ELSE
        -- Streak broken - reset to 1
        UPDATE public.user_activity_stats
        SET current_cooking_streak = 1,
            last_cook_date = v_today,
            updated_at = now()
        WHERE user_id = p_user_id;

        current_streak := 1;
        longest_streak := v_longest_streak;
    END IF;

    is_milestone := v_is_milestone;
    milestone_days := v_milestone_days;
    RETURN NEXT;
END;
$$;

COMMENT ON FUNCTION public.update_cooking_streak IS 'Update cooking streak when user completes a cooking session. Returns milestone info for notifications.';

-- Function to get users eligible for cook tonight notification
CREATE OR REPLACE FUNCTION public.get_cook_tonight_eligible_users(p_current_hour INTEGER)
RETURNS TABLE(
    user_id UUID,
    recipe_id UUID,
    recipe_title TEXT,
    is_active_user BOOLEAN
)
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
BEGIN
    RETURN QUERY
    SELECT DISTINCT ON (u.id)
        u.id as user_id,
        r.id as recipe_id,
        r.title as recipe_title,
        (uas.last_app_open_at > now() - INTERVAL '7 days') as is_active_user
    FROM public.users u
    JOIN public.push_tokens pt ON pt.user_id = u.id AND pt.is_active = true
    LEFT JOIN public.notification_preferences np ON np.user_id = u.id
    LEFT JOIN public.user_activity_stats uas ON uas.user_id = u.id
    -- Get an uncooked recipe from their collection
    JOIN public.user_recipe_data urd ON urd.user_id = u.id AND COALESCE(urd.times_cooked, 0) = 0
    JOIN public.recipes r ON r.id = urd.recipe_id AND r.is_draft = false
    WHERE
        -- Check notification preferences
        COALESCE(np.notifications_enabled, true) = true
        AND COALESCE(np.cook_tonight, true) = true
        -- Check timing: either matches preferred hour or use default (17:00)
        AND (
            COALESCE(uas.preferred_notification_hour, 17) = p_current_hour
            OR (uas.preferred_notification_hour IS NULL AND p_current_hour = 17)
        )
        -- Not recently active (at least 4 hours since last app open)
        AND (uas.last_app_open_at IS NULL OR uas.last_app_open_at < now() - INTERVAL '4 hours')
        -- Frequency check: active users can get daily, inactive get weekly
        AND (
            -- Active user (opened app in last 7 days): no frequency limit
            (uas.last_app_open_at > now() - INTERVAL '7 days')
            OR
            -- Inactive user: only send once per week
            (
                uas.last_app_open_at <= now() - INTERVAL '7 days'
                AND (uas.last_cook_tonight_sent_at IS NULL OR uas.last_cook_tonight_sent_at < now() - INTERVAL '7 days')
            )
        )
    ORDER BY u.id, random();
END;
$$;

COMMENT ON FUNCTION public.get_cook_tonight_eligible_users IS 'Get users eligible for cook tonight notification at the given hour. Respects preferences and frequency limits.';

-- Function to initialize notification preferences
CREATE OR REPLACE FUNCTION public.initialize_notification_preferences(p_user_id UUID)
RETURNS public.notification_preferences
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
DECLARE
    v_prefs public.notification_preferences;
BEGIN
    INSERT INTO public.notification_preferences (user_id)
    VALUES (p_user_id)
    ON CONFLICT (user_id) DO NOTHING
    RETURNING * INTO v_prefs;

    -- If insert was skipped due to conflict, fetch existing
    IF v_prefs IS NULL THEN
        SELECT * INTO v_prefs FROM public.notification_preferences WHERE user_id = p_user_id;
    END IF;

    RETURN v_prefs;
END;
$$;

COMMENT ON FUNCTION public.initialize_notification_preferences IS 'Creates default notification preferences for a user if they dont exist';
