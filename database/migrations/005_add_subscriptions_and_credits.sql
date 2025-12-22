-- Migration: 005_add_subscriptions_and_credits
-- Description: Add tables for RevenueCat subscriptions, user credits system, and referral program
-- This enables premium subscriptions and a credit-based extraction system for free users.

-- ============================================================================
-- USER SUBSCRIPTIONS (synced from RevenueCat)
-- ============================================================================
CREATE TABLE IF NOT EXISTS public.user_subscriptions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,
    revenuecat_customer_id TEXT NOT NULL,
    product_id TEXT,                          -- e.g., 'cuisto_pro_monthly', 'cuisto_pro_yearly'
    entitlement_id TEXT,                      -- e.g., 'pro'
    is_active BOOLEAN DEFAULT false,
    expires_at TIMESTAMP WITH TIME ZONE,
    original_purchase_date TIMESTAMP WITH TIME ZONE,
    is_trial BOOLEAN DEFAULT false,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
    UNIQUE(user_id)
);

COMMENT ON TABLE public.user_subscriptions IS 'User subscription status synced from RevenueCat';
COMMENT ON COLUMN public.user_subscriptions.product_id IS 'RevenueCat product identifier (e.g., cuisto_pro_monthly, cuisto_pro_yearly)';
COMMENT ON COLUMN public.user_subscriptions.entitlement_id IS 'RevenueCat entitlement identifier (e.g., pro)';
COMMENT ON COLUMN public.user_subscriptions.is_trial IS 'Whether user is currently in trial period';

-- ============================================================================
-- USER CREDITS (weekly standard credits + referral bonus credits)
-- ============================================================================
CREATE TABLE IF NOT EXISTS public.user_credits (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,
    standard_credits INTEGER DEFAULT 5,       -- Weekly credits (5 first week, then 3)
    referral_credits INTEGER DEFAULT 0,       -- Accumulated referral bonus credits
    credits_reset_at TIMESTAMP WITH TIME ZONE DEFAULT (date_trunc('week', now() AT TIME ZONE 'UTC') + INTERVAL '1 week'),
    first_week_ends_at TIMESTAMP WITH TIME ZONE,  -- Set on account creation, NULL = first week still active
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
    UNIQUE(user_id)
);

COMMENT ON TABLE public.user_credits IS 'User credit balance for extractions. Free users get weekly credits that reset.';
COMMENT ON COLUMN public.user_credits.standard_credits IS 'Weekly credits: 5 during first week, then 3. Reset weekly on Monday UTC.';
COMMENT ON COLUMN public.user_credits.referral_credits IS 'Bonus credits from referrals. Do not reset, but expire after 30 days.';
COMMENT ON COLUMN public.user_credits.credits_reset_at IS 'Next credit reset time (Monday 00:00 UTC)';
COMMENT ON COLUMN public.user_credits.first_week_ends_at IS 'When first week ends. NULL means first week is still active.';

-- ============================================================================
-- REFERRAL CODES
-- ============================================================================
CREATE TABLE IF NOT EXISTS public.referral_codes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,
    code TEXT NOT NULL UNIQUE,                -- e.g., 'CUISTO7X' (8-char alphanumeric)
    uses_count INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
    UNIQUE(user_id)
);

COMMENT ON TABLE public.referral_codes IS 'Unique referral codes for each user';
COMMENT ON COLUMN public.referral_codes.code IS '8-character alphanumeric referral code';
COMMENT ON COLUMN public.referral_codes.uses_count IS 'Number of times this code has been used';

-- ============================================================================
-- REFERRAL REDEMPTIONS (tracks who used whose code)
-- ============================================================================
CREATE TABLE IF NOT EXISTS public.referral_redemptions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    referrer_user_id UUID NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,
    referee_user_id UUID NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,
    referral_code_id UUID NOT NULL REFERENCES public.referral_codes(id),
    credits_awarded INTEGER DEFAULT 5,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
    UNIQUE(referee_user_id)                   -- User can only use one referral code ever
);

COMMENT ON TABLE public.referral_redemptions IS 'Records of referral code redemptions';
COMMENT ON COLUMN public.referral_redemptions.credits_awarded IS 'Credits given to both referrer and referee';

-- ============================================================================
-- REFERRAL CREDIT GRANTS (tracks individual referral credits with expiry)
-- ============================================================================
CREATE TABLE IF NOT EXISTS public.referral_credit_grants (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,
    amount INTEGER NOT NULL,                  -- Original amount granted
    remaining INTEGER NOT NULL,               -- Remaining credits (decrements on use)
    source TEXT NOT NULL,                     -- 'referrer' or 'referee'
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,  -- 30 days from grant
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now()
);

COMMENT ON TABLE public.referral_credit_grants IS 'Individual referral credit grants with expiration tracking';
COMMENT ON COLUMN public.referral_credit_grants.remaining IS 'Credits remaining from this grant. Use oldest grants first.';
COMMENT ON COLUMN public.referral_credit_grants.source IS 'Whether this grant was from being a referrer or referee';
COMMENT ON COLUMN public.referral_credit_grants.expires_at IS '30 days after grant creation';

-- ============================================================================
-- CREDIT TRANSACTIONS (audit log)
-- ============================================================================
CREATE TABLE IF NOT EXISTS public.credit_transactions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,
    amount INTEGER NOT NULL,                  -- Positive = add, negative = deduct
    credit_type TEXT NOT NULL,                -- 'standard' or 'referral'
    reason TEXT NOT NULL,                     -- 'extraction', 'weekly_reset', 'referral_bonus', 'expired'
    extraction_job_id UUID REFERENCES public.extraction_jobs(id),
    balance_after INTEGER NOT NULL,           -- Balance after this transaction
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now()
);

COMMENT ON TABLE public.credit_transactions IS 'Audit log of all credit changes';
COMMENT ON COLUMN public.credit_transactions.amount IS 'Positive for additions, negative for deductions';
COMMENT ON COLUMN public.credit_transactions.credit_type IS 'standard = weekly credits, referral = bonus credits';
COMMENT ON COLUMN public.credit_transactions.reason IS 'Why credits changed: extraction, weekly_reset, referral_bonus, expired';

-- ============================================================================
-- INDEXES
-- ============================================================================
CREATE INDEX IF NOT EXISTS idx_user_subscriptions_user_id ON public.user_subscriptions(user_id);
CREATE INDEX IF NOT EXISTS idx_user_subscriptions_active ON public.user_subscriptions(is_active) WHERE is_active = true;
CREATE INDEX IF NOT EXISTS idx_user_subscriptions_revenuecat ON public.user_subscriptions(revenuecat_customer_id);

CREATE INDEX IF NOT EXISTS idx_user_credits_user_id ON public.user_credits(user_id);
CREATE INDEX IF NOT EXISTS idx_user_credits_reset ON public.user_credits(credits_reset_at);

CREATE INDEX IF NOT EXISTS idx_referral_codes_code ON public.referral_codes(code);
CREATE INDEX IF NOT EXISTS idx_referral_codes_user ON public.referral_codes(user_id);

CREATE INDEX IF NOT EXISTS idx_referral_redemptions_referrer ON public.referral_redemptions(referrer_user_id);
CREATE INDEX IF NOT EXISTS idx_referral_redemptions_referee ON public.referral_redemptions(referee_user_id);

CREATE INDEX IF NOT EXISTS idx_referral_credit_grants_user ON public.referral_credit_grants(user_id);
CREATE INDEX IF NOT EXISTS idx_referral_credit_grants_expiry ON public.referral_credit_grants(expires_at);
CREATE INDEX IF NOT EXISTS idx_referral_credit_grants_remaining ON public.referral_credit_grants(remaining) WHERE remaining > 0;

CREATE INDEX IF NOT EXISTS idx_credit_transactions_user ON public.credit_transactions(user_id);
CREATE INDEX IF NOT EXISTS idx_credit_transactions_created ON public.credit_transactions(created_at);

-- ============================================================================
-- ROW LEVEL SECURITY
-- ============================================================================
ALTER TABLE public.user_subscriptions ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.user_credits ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.referral_codes ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.referral_redemptions ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.referral_credit_grants ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.credit_transactions ENABLE ROW LEVEL SECURITY;

-- Users can only view their own subscription
CREATE POLICY "Users can view own subscription"
    ON public.user_subscriptions FOR SELECT
    USING (auth.uid() = user_id);

-- Users can only view their own credits
CREATE POLICY "Users can view own credits"
    ON public.user_credits FOR SELECT
    USING (auth.uid() = user_id);

-- Users can view their own referral code
CREATE POLICY "Users can view own referral code"
    ON public.referral_codes FOR SELECT
    USING (auth.uid() = user_id);

-- Anyone can validate referral codes (needed for code entry)
CREATE POLICY "Anyone can validate referral codes"
    ON public.referral_codes FOR SELECT
    USING (true);

-- Users can view their own referral redemptions
CREATE POLICY "Users can view own referral redemptions"
    ON public.referral_redemptions FOR SELECT
    USING (auth.uid() = referrer_user_id OR auth.uid() = referee_user_id);

-- Users can view their own referral credit grants
CREATE POLICY "Users can view own referral credit grants"
    ON public.referral_credit_grants FOR SELECT
    USING (auth.uid() = user_id);

-- Users can view their own credit transactions
CREATE POLICY "Users can view own credit transactions"
    ON public.credit_transactions FOR SELECT
    USING (auth.uid() = user_id);

-- ============================================================================
-- FUNCTIONS
-- ============================================================================

-- Function to calculate next Monday 00:00 UTC
CREATE OR REPLACE FUNCTION public.next_monday_utc()
RETURNS TIMESTAMP WITH TIME ZONE
LANGUAGE sql
IMMUTABLE
AS $$
    SELECT date_trunc('week', now() AT TIME ZONE 'UTC') + INTERVAL '1 week';
$$;

-- Function to initialize user credits (called when user first needs credits)
CREATE OR REPLACE FUNCTION public.initialize_user_credits(p_user_id UUID)
RETURNS public.user_credits
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
DECLARE
    v_credits public.user_credits;
BEGIN
    INSERT INTO public.user_credits (user_id, standard_credits, referral_credits, credits_reset_at, first_week_ends_at)
    VALUES (
        p_user_id,
        5,  -- First week gets 5 credits
        0,
        public.next_monday_utc(),
        now() + INTERVAL '7 days'  -- First week ends in 7 days
    )
    ON CONFLICT (user_id) DO NOTHING
    RETURNING * INTO v_credits;

    -- If insert was skipped due to conflict, fetch existing
    IF v_credits IS NULL THEN
        SELECT * INTO v_credits FROM public.user_credits WHERE user_id = p_user_id;
    END IF;

    RETURN v_credits;
END;
$$;

-- Function to generate a unique referral code
CREATE OR REPLACE FUNCTION public.generate_referral_code(p_user_id UUID)
RETURNS TEXT
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
DECLARE
    v_code TEXT;
    v_exists BOOLEAN;
BEGIN
    -- Check if user already has a code
    SELECT code INTO v_code FROM public.referral_codes WHERE user_id = p_user_id;
    IF v_code IS NOT NULL THEN
        RETURN v_code;
    END IF;

    -- Generate unique 8-char alphanumeric code
    LOOP
        v_code := upper(substring(md5(random()::text || clock_timestamp()::text) from 1 for 8));
        SELECT EXISTS(SELECT 1 FROM public.referral_codes WHERE code = v_code) INTO v_exists;
        EXIT WHEN NOT v_exists;
    END LOOP;

    -- Insert the new code
    INSERT INTO public.referral_codes (user_id, code)
    VALUES (p_user_id, v_code);

    RETURN v_code;
END;
$$;

COMMENT ON FUNCTION public.next_monday_utc IS 'Returns the timestamp of next Monday 00:00 UTC';
COMMENT ON FUNCTION public.initialize_user_credits IS 'Creates initial credit record for a user with first-week bonus';
COMMENT ON FUNCTION public.generate_referral_code IS 'Generates or returns existing 8-char referral code for user';
