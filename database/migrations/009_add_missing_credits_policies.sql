-- Migration: 009_add_missing_credits_policies
-- Description: Add missing INSERT/UPDATE policies for credits and referral tables
-- These policies are needed for the SECURITY DEFINER functions to work properly
-- and for the backend service to manage credits.

-- ============================================================================
-- USER CREDITS POLICIES
-- ============================================================================

-- Allow INSERT for user_credits (used by initialize_user_credits function)
CREATE POLICY "Service can insert user credits"
    ON public.user_credits FOR INSERT
    WITH CHECK (auth.uid() = user_id);

-- Allow UPDATE for user_credits (used by credit deduction and reset)
CREATE POLICY "Service can update own credits"
    ON public.user_credits FOR UPDATE
    USING (auth.uid() = user_id)
    WITH CHECK (auth.uid() = user_id);

-- ============================================================================
-- REFERRAL CODES POLICIES
-- ============================================================================

-- Allow INSERT for referral_codes (used by generate_referral_code function)
CREATE POLICY "Service can insert referral codes"
    ON public.referral_codes FOR INSERT
    WITH CHECK (auth.uid() = user_id);

-- ============================================================================
-- REFERRAL CREDIT GRANTS POLICIES
-- ============================================================================

-- Allow INSERT for referral_credit_grants (used when awarding referral bonuses)
CREATE POLICY "Service can insert referral credit grants"
    ON public.referral_credit_grants FOR INSERT
    WITH CHECK (auth.uid() = user_id);

-- Allow UPDATE for referral_credit_grants (used when deducting referral credits)
CREATE POLICY "Service can update own referral credit grants"
    ON public.referral_credit_grants FOR UPDATE
    USING (auth.uid() = user_id)
    WITH CHECK (auth.uid() = user_id);

-- Allow DELETE for referral_credit_grants (used when credits are depleted or expired)
CREATE POLICY "Service can delete own referral credit grants"
    ON public.referral_credit_grants FOR DELETE
    USING (auth.uid() = user_id);

-- ============================================================================
-- REFERRAL REDEMPTIONS POLICIES
-- ============================================================================

-- Allow INSERT for referral_redemptions (used when redeeming a referral code)
CREATE POLICY "Service can insert referral redemptions"
    ON public.referral_redemptions FOR INSERT
    WITH CHECK (auth.uid() = referee_user_id);

-- ============================================================================
-- CREDIT TRANSACTIONS POLICIES
-- ============================================================================

-- Allow INSERT for credit_transactions (audit logging)
CREATE POLICY "Service can insert credit transactions"
    ON public.credit_transactions FOR INSERT
    WITH CHECK (auth.uid() = user_id);

-- ============================================================================
-- USER SUBSCRIPTIONS POLICIES
-- ============================================================================

-- Allow INSERT for user_subscriptions (created on first RevenueCat sync)
CREATE POLICY "Service can insert user subscriptions"
    ON public.user_subscriptions FOR INSERT
    WITH CHECK (auth.uid() = user_id);

-- Allow UPDATE for user_subscriptions (updated by RevenueCat webhooks)
CREATE POLICY "Service can update own subscriptions"
    ON public.user_subscriptions FOR UPDATE
    USING (auth.uid() = user_id)
    WITH CHECK (auth.uid() = user_id);
