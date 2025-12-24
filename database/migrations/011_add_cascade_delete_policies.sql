-- Migration: 011_add_cascade_delete_policies
-- Description: Add DELETE policies to allow CASCADE deletes when auth.users is deleted
-- The issue is that when Supabase admin.delete_user() is called, it triggers CASCADE deletes
-- but RLS policies block them because auth.uid() is NULL during CASCADE operations.
--
-- Solution: For tables that reference public.users (not auth.users directly), we need to
-- either add DELETE policies or ensure the service role can bypass RLS.
--
-- Tables that reference public.users and need DELETE policies:
-- - referral_codes (user_id -> users.id)
-- - referral_redemptions (referrer_user_id, referee_user_id -> users.id)
-- - referral_credit_grants (user_id -> users.id)
-- - credit_transactions (user_id -> users.id)
-- - user_credits (user_id -> users.id)
-- - user_subscriptions (user_id -> users.id)

-- ============================================================================
-- USER CREDITS - DELETE POLICY
-- ============================================================================
CREATE POLICY "Allow cascade delete on user_credits"
    ON public.user_credits FOR DELETE
    USING (true);

-- ============================================================================
-- REFERRAL CODES - DELETE POLICY
-- ============================================================================
CREATE POLICY "Allow cascade delete on referral_codes"
    ON public.referral_codes FOR DELETE
    USING (true);

-- ============================================================================
-- REFERRAL REDEMPTIONS - DELETE POLICY
-- ============================================================================
CREATE POLICY "Allow cascade delete on referral_redemptions"
    ON public.referral_redemptions FOR DELETE
    USING (true);

-- ============================================================================
-- REFERRAL CREDIT GRANTS - Already has delete policy but let's ensure it works for cascade
-- ============================================================================
-- Drop existing policy if it only allows auth.uid() = user_id
DROP POLICY IF EXISTS "Service can delete own referral credit grants" ON public.referral_credit_grants;

CREATE POLICY "Allow cascade delete on referral_credit_grants"
    ON public.referral_credit_grants FOR DELETE
    USING (true);

-- ============================================================================
-- CREDIT TRANSACTIONS - DELETE POLICY
-- ============================================================================
CREATE POLICY "Allow cascade delete on credit_transactions"
    ON public.credit_transactions FOR DELETE
    USING (true);

-- ============================================================================
-- USER SUBSCRIPTIONS - DELETE POLICY
-- ============================================================================
CREATE POLICY "Allow cascade delete on user_subscriptions"
    ON public.user_subscriptions FOR DELETE
    USING (true);

-- ============================================================================
-- USERS TABLE - DELETE POLICY (for CASCADE from auth.users)
-- ============================================================================
CREATE POLICY "Allow cascade delete on users"
    ON public.users FOR DELETE
    USING (true);

-- ============================================================================
-- ADDITIONAL TABLES THAT REFERENCE auth.users DIRECTLY
-- These also need DELETE policies for CASCADE to work
-- ============================================================================

-- COOKBOOKS
CREATE POLICY "Allow cascade delete on cookbooks"
    ON public.cookbooks FOR DELETE
    USING (true);

-- EXTRACTION_JOBS
CREATE POLICY "Allow cascade delete on extraction_jobs"
    ON public.extraction_jobs FOR DELETE
    USING (true);

-- RECIPE_CONTRIBUTORS (uses SET NULL but still needs policy for the update)
CREATE POLICY "Allow cascade delete on recipe_contributors"
    ON public.recipe_contributors FOR DELETE
    USING (true);

-- RECIPE_COOKING_EVENTS
CREATE POLICY "Allow cascade delete on recipe_cooking_events"
    ON public.recipe_cooking_events FOR DELETE
    USING (true);

-- USER_ONBOARDING
CREATE POLICY "Allow cascade delete on user_onboarding"
    ON public.user_onboarding FOR DELETE
    USING (true);

-- USER_PREFERENCES
CREATE POLICY "Allow cascade delete on user_preferences"
    ON public.user_preferences FOR DELETE
    USING (true);

-- USER_RECIPE_DATA
CREATE POLICY "Allow cascade delete on user_recipe_data"
    ON public.user_recipe_data FOR DELETE
    USING (true);

-- ============================================================================
-- TABLES WITH NESTED FOREIGN KEYS (depend on cookbooks/recipes being deleted)
-- ============================================================================

-- COOKBOOK_FOLDERS (references cookbooks)
CREATE POLICY "Allow cascade delete on cookbook_folders"
    ON public.cookbook_folders FOR DELETE
    USING (true);

-- COOKBOOK_RECIPES (references cookbooks and recipes)
CREATE POLICY "Allow cascade delete on cookbook_recipes"
    ON public.cookbook_recipes FOR DELETE
    USING (true);

-- FOLDER_RECIPES (references cookbook_folders)
CREATE POLICY "Allow cascade delete on folder_recipes"
    ON public.folder_recipes FOR DELETE
    USING (true);
