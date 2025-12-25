-- Migration: 010_auto_create_public_user
-- Description: Automatically create public.users record when auth.users is created
-- This fixes the foreign key issue where user_credits references public.users,
-- but public.users was only created during onboarding (too late).

-- ============================================================================
-- FUNCTION: Auto-create public.users record
-- ============================================================================
CREATE OR REPLACE FUNCTION public.handle_new_user()
RETURNS TRIGGER
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public
AS $$
BEGIN
    INSERT INTO public.users (id, name, onboarding_completed, created_at, updated_at)
    VALUES (
        NEW.id,
        COALESCE(
            NEW.raw_user_meta_data->>'name',
            SPLIT_PART(NEW.email, '@', 1),
            'User'
        ),
        false,
        NOW(),
        NOW()
    )
    ON CONFLICT (id) DO NOTHING;

    RETURN NEW;
END;
$$;

-- ============================================================================
-- TRIGGER: Create public.users on auth.users insert
-- ============================================================================
DROP TRIGGER IF EXISTS on_auth_user_created ON auth.users;

CREATE TRIGGER on_auth_user_created
    AFTER INSERT ON auth.users
    FOR EACH ROW
    EXECUTE FUNCTION public.handle_new_user();

-- ============================================================================
-- BACKFILL: Create public.users for any existing auth.users without one
-- ============================================================================
INSERT INTO public.users (id, name, onboarding_completed, created_at, updated_at)
SELECT
    au.id,
    COALESCE(
        au.raw_user_meta_data->>'name',
        SPLIT_PART(au.email, '@', 1),
        'User'
    ),
    false,
    COALESCE(au.created_at, NOW()),
    NOW()
FROM auth.users au
LEFT JOIN public.users pu ON au.id = pu.id
WHERE pu.id IS NULL;

COMMENT ON FUNCTION public.handle_new_user IS 'Automatically creates a public.users record when a new auth.users record is created. This ensures foreign key constraints to public.users can always be satisfied.';
