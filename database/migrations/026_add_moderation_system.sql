-- Migration: 026_add_moderation_system
-- Description: Add tables for content reporting, extraction feedback, and user moderation
-- This enables users to report inappropriate content and provides tools for moderators.

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
-- ADD COLUMNS TO EXISTING TABLES
-- ============================================================================

-- Add is_admin column to users table
ALTER TABLE public.users
ADD COLUMN IF NOT EXISTS is_admin BOOLEAN DEFAULT false;

COMMENT ON COLUMN public.users.is_admin IS 'User has admin/moderator privileges';

-- Add moderation columns to recipes table
ALTER TABLE public.recipes
ADD COLUMN IF NOT EXISTS is_hidden BOOLEAN DEFAULT false,
ADD COLUMN IF NOT EXISTS hidden_at TIMESTAMP WITH TIME ZONE,
ADD COLUMN IF NOT EXISTS hidden_reason TEXT;

COMMENT ON COLUMN public.recipes.is_hidden IS 'Recipe hidden from public view by moderators';
COMMENT ON COLUMN public.recipes.hidden_at IS 'When the recipe was hidden';
COMMENT ON COLUMN public.recipes.hidden_reason IS 'Reason for hiding the recipe';

-- ============================================================================
-- CONTENT REPORTS TABLE
-- ============================================================================
CREATE TABLE IF NOT EXISTS public.content_reports (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- What is being reported
    recipe_id UUID NOT NULL REFERENCES public.recipes(id) ON DELETE CASCADE,

    -- Who reported it
    reporter_user_id UUID NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,

    -- Report details
    reason VARCHAR(50) NOT NULL,
    description TEXT,

    -- Status tracking
    status VARCHAR(20) DEFAULT 'pending' NOT NULL,
    priority INTEGER DEFAULT 0,

    -- Resolution
    resolved_by UUID REFERENCES public.users(id),
    resolved_at TIMESTAMP WITH TIME ZONE,
    resolution_notes TEXT,

    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT now(),

    -- Constraints
    CONSTRAINT content_reports_reason_check CHECK (reason IN (
        'inappropriate_content',
        'hate_speech',
        'copyright_violation',
        'spam_advertising',
        'misinformation',
        'other'
    )),
    CONSTRAINT content_reports_status_check CHECK (status IN (
        'pending',
        'in_review',
        'resolved',
        'escalated'
    )),
    -- Prevent duplicate reports from same user on same recipe (while pending/in_review)
    CONSTRAINT content_reports_unique_pending UNIQUE (recipe_id, reporter_user_id)
);

COMMENT ON TABLE public.content_reports IS 'User reports for inappropriate recipe content';
COMMENT ON COLUMN public.content_reports.priority IS 'Calculated priority: hate_speech=10, copyright=8, misinformation=6, etc.';
COMMENT ON COLUMN public.content_reports.reason IS 'Report reason: inappropriate_content, hate_speech, copyright_violation, spam_advertising, misinformation, other';
COMMENT ON COLUMN public.content_reports.status IS 'Report status: pending, in_review, resolved, escalated';

-- ============================================================================
-- EXTRACTION FEEDBACK TABLE
-- ============================================================================
CREATE TABLE IF NOT EXISTS public.extraction_feedback (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- What recipe has issues
    recipe_id UUID NOT NULL REFERENCES public.recipes(id) ON DELETE CASCADE,

    -- Who submitted feedback
    user_id UUID NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,

    -- Feedback details
    category VARCHAR(50) NOT NULL,
    description TEXT,

    -- Optional: link to extraction job for debugging
    extraction_job_id UUID REFERENCES public.extraction_jobs(id) ON DELETE SET NULL,

    -- Status tracking
    status VARCHAR(20) DEFAULT 'pending' NOT NULL,

    -- Resolution
    resolved_by UUID REFERENCES public.users(id),
    resolved_at TIMESTAMP WITH TIME ZONE,
    resolution_notes TEXT,
    was_helpful BOOLEAN,

    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT now(),

    -- Constraints
    CONSTRAINT extraction_feedback_category_check CHECK (category IN (
        'wrong_ingredients',
        'missing_steps',
        'incorrect_steps',
        'bad_formatting',
        'wrong_measurements',
        'wrong_servings',
        'ai_hallucination',
        'wrong_title',
        'wrong_image',
        'other'
    )),
    CONSTRAINT extraction_feedback_status_check CHECK (status IN (
        'pending',
        'in_review',
        'resolved',
        'escalated'
    )),
    -- Allow multiple feedback items per user per recipe (different categories)
    CONSTRAINT extraction_feedback_unique_category UNIQUE (recipe_id, user_id, category)
);

COMMENT ON TABLE public.extraction_feedback IS 'User feedback on AI extraction quality for improvement';
COMMENT ON COLUMN public.extraction_feedback.category IS 'Feedback category: wrong_ingredients, missing_steps, incorrect_steps, bad_formatting, wrong_measurements, wrong_servings, ai_hallucination, wrong_title, wrong_image, other';
COMMENT ON COLUMN public.extraction_feedback.was_helpful IS 'Whether this feedback helped improve the system';

-- ============================================================================
-- USER MODERATION STATUS TABLE
-- ============================================================================
CREATE TABLE IF NOT EXISTS public.user_moderation (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES public.users(id) ON DELETE CASCADE UNIQUE,

    -- Current status
    status VARCHAR(20) DEFAULT 'good_standing' NOT NULL,

    -- Counters
    warning_count INTEGER DEFAULT 0,
    report_count INTEGER DEFAULT 0,
    false_report_count INTEGER DEFAULT 0,

    -- Suspension details
    suspended_until TIMESTAMP WITH TIME ZONE,
    ban_reason TEXT,

    -- Reporter reliability score (0-100)
    reporter_reliability_score INTEGER DEFAULT 100,

    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT now(),

    -- Constraints
    CONSTRAINT user_moderation_status_check CHECK (status IN (
        'good_standing',
        'warned',
        'suspended',
        'banned'
    )),
    CONSTRAINT user_moderation_reliability_check CHECK (
        reporter_reliability_score >= 0 AND reporter_reliability_score <= 100
    )
);

COMMENT ON TABLE public.user_moderation IS 'Tracks user moderation status, warnings, and reporter reliability';
COMMENT ON COLUMN public.user_moderation.status IS 'User status: good_standing, warned, suspended, banned';
COMMENT ON COLUMN public.user_moderation.report_count IS 'Number of times this users content was reported';
COMMENT ON COLUMN public.user_moderation.false_report_count IS 'Number of false reports submitted by user';
COMMENT ON COLUMN public.user_moderation.reporter_reliability_score IS 'Score 0-100 based on accuracy of reports. <50 = limited reporting';

-- ============================================================================
-- MODERATION ACTIONS LOG (AUDIT TRAIL)
-- ============================================================================
CREATE TABLE IF NOT EXISTS public.moderation_actions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Who performed the action
    moderator_id UUID NOT NULL REFERENCES public.users(id),

    -- Action details
    action_type VARCHAR(30) NOT NULL,

    -- References (at least one should be set)
    target_user_id UUID REFERENCES public.users(id) ON DELETE SET NULL,
    target_recipe_id UUID REFERENCES public.recipes(id) ON DELETE SET NULL,
    content_report_id UUID REFERENCES public.content_reports(id) ON DELETE SET NULL,
    extraction_feedback_id UUID REFERENCES public.extraction_feedback(id) ON DELETE SET NULL,

    -- Details
    reason TEXT NOT NULL,
    notes TEXT,

    -- For suspensions
    duration_days INTEGER,

    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now(),

    -- Constraints
    CONSTRAINT moderation_actions_type_check CHECK (action_type IN (
        'dismiss_report',
        'hide_recipe',
        'unhide_recipe',
        'warn_user',
        'suspend_user',
        'unsuspend_user',
        'ban_user',
        'unban_user',
        'resolve_feedback'
    ))
);

COMMENT ON TABLE public.moderation_actions IS 'Audit log of all moderation actions for accountability';
COMMENT ON COLUMN public.moderation_actions.action_type IS 'Action type: dismiss_report, hide_recipe, unhide_recipe, warn_user, suspend_user, unsuspend_user, ban_user, unban_user, resolve_feedback';
COMMENT ON COLUMN public.moderation_actions.duration_days IS 'Duration in days for suspensions. NULL for permanent bans.';

-- ============================================================================
-- USER WARNINGS TABLE
-- ============================================================================
CREATE TABLE IF NOT EXISTS public.user_warnings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    user_id UUID NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,
    issued_by UUID NOT NULL REFERENCES public.users(id),

    reason TEXT NOT NULL,
    content_report_id UUID REFERENCES public.content_reports(id) ON DELETE SET NULL,
    recipe_id UUID REFERENCES public.recipes(id) ON DELETE SET NULL,

    -- Acknowledgment
    acknowledged_at TIMESTAMP WITH TIME ZONE,

    created_at TIMESTAMP WITH TIME ZONE DEFAULT now()
);

COMMENT ON TABLE public.user_warnings IS 'Warnings issued to users with optional acknowledgment tracking';

-- ============================================================================
-- APPEALS TABLE (Future: Allow users to appeal moderation decisions)
-- ============================================================================
CREATE TABLE IF NOT EXISTS public.moderation_appeals (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    user_id UUID NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,
    moderation_action_id UUID NOT NULL REFERENCES public.moderation_actions(id),

    appeal_reason TEXT NOT NULL,

    status VARCHAR(20) DEFAULT 'pending' NOT NULL,

    reviewed_by UUID REFERENCES public.users(id),
    reviewed_at TIMESTAMP WITH TIME ZONE,
    review_notes TEXT,
    appeal_granted BOOLEAN,

    created_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT now(),

    -- Constraints
    CONSTRAINT moderation_appeals_status_check CHECK (status IN (
        'pending',
        'in_review',
        'resolved',
        'escalated'
    ))
);

COMMENT ON TABLE public.moderation_appeals IS 'User appeals against moderation decisions';

-- ============================================================================
-- INDEXES
-- ============================================================================

-- Content reports indexes
CREATE INDEX IF NOT EXISTS idx_content_reports_status ON public.content_reports(status);
CREATE INDEX IF NOT EXISTS idx_content_reports_recipe ON public.content_reports(recipe_id);
CREATE INDEX IF NOT EXISTS idx_content_reports_reporter ON public.content_reports(reporter_user_id);
CREATE INDEX IF NOT EXISTS idx_content_reports_priority ON public.content_reports(priority DESC) WHERE status = 'pending';
CREATE INDEX IF NOT EXISTS idx_content_reports_created ON public.content_reports(created_at DESC);

-- Extraction feedback indexes
CREATE INDEX IF NOT EXISTS idx_extraction_feedback_status ON public.extraction_feedback(status);
CREATE INDEX IF NOT EXISTS idx_extraction_feedback_recipe ON public.extraction_feedback(recipe_id);
CREATE INDEX IF NOT EXISTS idx_extraction_feedback_user ON public.extraction_feedback(user_id);
CREATE INDEX IF NOT EXISTS idx_extraction_feedback_created ON public.extraction_feedback(created_at DESC);

-- User moderation indexes
CREATE INDEX IF NOT EXISTS idx_user_moderation_status ON public.user_moderation(status);
CREATE INDEX IF NOT EXISTS idx_user_moderation_user ON public.user_moderation(user_id);

-- Moderation actions indexes
CREATE INDEX IF NOT EXISTS idx_moderation_actions_moderator ON public.moderation_actions(moderator_id);
CREATE INDEX IF NOT EXISTS idx_moderation_actions_target_user ON public.moderation_actions(target_user_id);
CREATE INDEX IF NOT EXISTS idx_moderation_actions_target_recipe ON public.moderation_actions(target_recipe_id);
CREATE INDEX IF NOT EXISTS idx_moderation_actions_created ON public.moderation_actions(created_at DESC);

-- User warnings indexes
CREATE INDEX IF NOT EXISTS idx_user_warnings_user ON public.user_warnings(user_id);
CREATE INDEX IF NOT EXISTS idx_user_warnings_created ON public.user_warnings(created_at DESC);

-- Appeals indexes
CREATE INDEX IF NOT EXISTS idx_moderation_appeals_user ON public.moderation_appeals(user_id);
CREATE INDEX IF NOT EXISTS idx_moderation_appeals_status ON public.moderation_appeals(status);

-- Recipes hidden index
CREATE INDEX IF NOT EXISTS idx_recipes_hidden ON public.recipes(is_hidden) WHERE is_hidden = true;

-- ============================================================================
-- ROW LEVEL SECURITY
-- ============================================================================
ALTER TABLE public.content_reports ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.extraction_feedback ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.user_moderation ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.moderation_actions ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.user_warnings ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.moderation_appeals ENABLE ROW LEVEL SECURITY;

-- ============================================================================
-- CONTENT REPORTS RLS POLICIES
-- ============================================================================

-- Users can create content reports
CREATE POLICY "Users can create content reports"
    ON public.content_reports FOR INSERT
    WITH CHECK (auth.uid() = reporter_user_id);

-- Users can view their own reports
CREATE POLICY "Users can view own reports"
    ON public.content_reports FOR SELECT
    USING (auth.uid() = reporter_user_id);

-- Admins can view all reports
CREATE POLICY "Admins can view all reports"
    ON public.content_reports FOR SELECT
    USING (EXISTS (SELECT 1 FROM public.users WHERE id = auth.uid() AND is_admin = true));

-- Admins can update reports
CREATE POLICY "Admins can update reports"
    ON public.content_reports FOR UPDATE
    USING (EXISTS (SELECT 1 FROM public.users WHERE id = auth.uid() AND is_admin = true));

-- ============================================================================
-- EXTRACTION FEEDBACK RLS POLICIES
-- ============================================================================

-- Users can create extraction feedback
CREATE POLICY "Users can create extraction feedback"
    ON public.extraction_feedback FOR INSERT
    WITH CHECK (auth.uid() = user_id);

-- Users can view their own feedback
CREATE POLICY "Users can view own feedback"
    ON public.extraction_feedback FOR SELECT
    USING (auth.uid() = user_id);

-- Admins can view all feedback
CREATE POLICY "Admins can view all feedback"
    ON public.extraction_feedback FOR SELECT
    USING (EXISTS (SELECT 1 FROM public.users WHERE id = auth.uid() AND is_admin = true));

-- Admins can update feedback
CREATE POLICY "Admins can update feedback"
    ON public.extraction_feedback FOR UPDATE
    USING (EXISTS (SELECT 1 FROM public.users WHERE id = auth.uid() AND is_admin = true));

-- ============================================================================
-- USER MODERATION RLS POLICIES
-- ============================================================================

-- Users can view their own moderation status
CREATE POLICY "Users can view own moderation status"
    ON public.user_moderation FOR SELECT
    USING (auth.uid() = user_id);

-- Admins can manage all user moderation records
CREATE POLICY "Admins can manage user moderation"
    ON public.user_moderation FOR ALL
    USING (EXISTS (SELECT 1 FROM public.users WHERE id = auth.uid() AND is_admin = true));

-- ============================================================================
-- MODERATION ACTIONS RLS POLICIES
-- ============================================================================

-- Users can view actions targeting them
CREATE POLICY "Users can view actions targeting them"
    ON public.moderation_actions FOR SELECT
    USING (auth.uid() = target_user_id);

-- Admins can manage all moderation actions
CREATE POLICY "Admins can manage moderation actions"
    ON public.moderation_actions FOR ALL
    USING (EXISTS (SELECT 1 FROM public.users WHERE id = auth.uid() AND is_admin = true));

-- ============================================================================
-- USER WARNINGS RLS POLICIES
-- ============================================================================

-- Users can view their own warnings
CREATE POLICY "Users can view own warnings"
    ON public.user_warnings FOR SELECT
    USING (auth.uid() = user_id);

-- Users can update their own warnings (for acknowledgment)
CREATE POLICY "Users can acknowledge own warnings"
    ON public.user_warnings FOR UPDATE
    USING (auth.uid() = user_id)
    WITH CHECK (auth.uid() = user_id);

-- Admins can manage all warnings
CREATE POLICY "Admins can manage warnings"
    ON public.user_warnings FOR ALL
    USING (EXISTS (SELECT 1 FROM public.users WHERE id = auth.uid() AND is_admin = true));

-- ============================================================================
-- MODERATION APPEALS RLS POLICIES
-- ============================================================================

-- Users can create appeals
CREATE POLICY "Users can create appeals"
    ON public.moderation_appeals FOR INSERT
    WITH CHECK (auth.uid() = user_id);

-- Users can view their own appeals
CREATE POLICY "Users can view own appeals"
    ON public.moderation_appeals FOR SELECT
    USING (auth.uid() = user_id);

-- Admins can manage all appeals
CREATE POLICY "Admins can manage appeals"
    ON public.moderation_appeals FOR ALL
    USING (EXISTS (SELECT 1 FROM public.users WHERE id = auth.uid() AND is_admin = true));

-- ============================================================================
-- FUNCTIONS
-- ============================================================================

-- Function to calculate report priority based on reason
CREATE OR REPLACE FUNCTION public.calculate_report_priority(reason VARCHAR(50))
RETURNS INTEGER
LANGUAGE sql
IMMUTABLE
AS $$
    SELECT CASE reason
        WHEN 'hate_speech' THEN 10
        WHEN 'copyright_violation' THEN 8
        WHEN 'misinformation' THEN 6
        WHEN 'inappropriate_content' THEN 4
        WHEN 'spam_advertising' THEN 2
        ELSE 1
    END;
$$;

COMMENT ON FUNCTION public.calculate_report_priority IS 'Calculates priority score for content reports based on reason severity';

-- Trigger to set priority on insert
CREATE OR REPLACE FUNCTION public.set_report_priority()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
BEGIN
    NEW.priority := public.calculate_report_priority(NEW.reason);
    RETURN NEW;
END;
$$;

DROP TRIGGER IF EXISTS trigger_set_report_priority ON public.content_reports;
CREATE TRIGGER trigger_set_report_priority
    BEFORE INSERT ON public.content_reports
    FOR EACH ROW
    EXECUTE FUNCTION public.set_report_priority();

-- Function to update updated_at timestamp
CREATE OR REPLACE FUNCTION public.update_moderation_timestamp()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
BEGIN
    NEW.updated_at := now();
    RETURN NEW;
END;
$$;

-- Triggers for updated_at
DROP TRIGGER IF EXISTS trigger_update_content_reports_timestamp ON public.content_reports;
CREATE TRIGGER trigger_update_content_reports_timestamp
    BEFORE UPDATE ON public.content_reports
    FOR EACH ROW
    EXECUTE FUNCTION public.update_moderation_timestamp();

DROP TRIGGER IF EXISTS trigger_update_extraction_feedback_timestamp ON public.extraction_feedback;
CREATE TRIGGER trigger_update_extraction_feedback_timestamp
    BEFORE UPDATE ON public.extraction_feedback
    FOR EACH ROW
    EXECUTE FUNCTION public.update_moderation_timestamp();

DROP TRIGGER IF EXISTS trigger_update_user_moderation_timestamp ON public.user_moderation;
CREATE TRIGGER trigger_update_user_moderation_timestamp
    BEFORE UPDATE ON public.user_moderation
    FOR EACH ROW
    EXECUTE FUNCTION public.update_moderation_timestamp();

DROP TRIGGER IF EXISTS trigger_update_moderation_appeals_timestamp ON public.moderation_appeals;
CREATE TRIGGER trigger_update_moderation_appeals_timestamp
    BEFORE UPDATE ON public.moderation_appeals
    FOR EACH ROW
    EXECUTE FUNCTION public.update_moderation_timestamp();

-- Function to check user report rate limit (max 10 reports per day)
CREATE OR REPLACE FUNCTION public.check_report_rate_limit(p_user_id UUID)
RETURNS BOOLEAN
LANGUAGE plpgsql
AS $$
DECLARE
    v_count INTEGER;
BEGIN
    SELECT COUNT(*) INTO v_count
    FROM public.content_reports
    WHERE reporter_user_id = p_user_id
    AND created_at > now() - INTERVAL '24 hours';

    RETURN v_count < 10;
END;
$$;

COMMENT ON FUNCTION public.check_report_rate_limit IS 'Returns true if user has submitted fewer than 10 reports in the last 24 hours';

-- Function to initialize user moderation record
CREATE OR REPLACE FUNCTION public.initialize_user_moderation(p_user_id UUID)
RETURNS public.user_moderation
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
DECLARE
    v_moderation public.user_moderation;
BEGIN
    INSERT INTO public.user_moderation (user_id)
    VALUES (p_user_id)
    ON CONFLICT (user_id) DO NOTHING
    RETURNING * INTO v_moderation;

    IF v_moderation IS NULL THEN
        SELECT * INTO v_moderation FROM public.user_moderation WHERE user_id = p_user_id;
    END IF;

    RETURN v_moderation;
END;
$$;

COMMENT ON FUNCTION public.initialize_user_moderation IS 'Creates or returns existing moderation record for a user';

-- Function to increment user report count (called when their content is reported)
CREATE OR REPLACE FUNCTION public.increment_user_report_count(p_user_id UUID)
RETURNS VOID
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
BEGIN
    -- Initialize moderation record if it doesn't exist
    PERFORM public.initialize_user_moderation(p_user_id);

    -- Increment report count
    UPDATE public.user_moderation
    SET report_count = report_count + 1,
        updated_at = now()
    WHERE user_id = p_user_id;
END;
$$;

COMMENT ON FUNCTION public.increment_user_report_count IS 'Increments the report count for a user whose content was reported';

-- Function to adjust reporter reliability score
CREATE OR REPLACE FUNCTION public.adjust_reporter_reliability(
    p_reporter_id UUID,
    p_adjustment INTEGER
)
RETURNS INTEGER
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
DECLARE
    v_new_score INTEGER;
BEGIN
    -- Initialize moderation record if it doesn't exist
    PERFORM public.initialize_user_moderation(p_reporter_id);

    -- Adjust score within bounds
    UPDATE public.user_moderation
    SET reporter_reliability_score = GREATEST(0, LEAST(100, reporter_reliability_score + p_adjustment)),
        updated_at = now()
    WHERE user_id = p_reporter_id
    RETURNING reporter_reliability_score INTO v_new_score;

    RETURN v_new_score;
END;
$$;

COMMENT ON FUNCTION public.adjust_reporter_reliability IS 'Adjusts reporter reliability score. Positive for valid reports, negative for false reports.';
