-- Seed script to create the first admin user
-- Run this AFTER creating the auth user in Supabase Dashboard or via CLI
--
-- STEP 1: Create auth user via Supabase Dashboard:
--   1. Go to Authentication → Users → Add User
--   2. Email: harry@cuisto.app
--   3. Password: (your chosen password)
--   4. Check "Auto Confirm User"
--
-- STEP 2: Run this SQL to set up the admin profile:

-- Ensure the user exists in public.users and mark as admin
INSERT INTO public.users (id, name, is_admin, onboarding_completed, profile_completed, created_at, updated_at)
SELECT
    au.id,
    'Harry',
    true,  -- is_admin
    true,  -- skip onboarding for admin
    true,  -- skip profile setup for admin
    NOW(),
    NOW()
FROM auth.users au
WHERE au.email = 'harry@cuisto.app'
ON CONFLICT (id) DO UPDATE SET
    is_admin = true,
    onboarding_completed = true,
    profile_completed = true,
    updated_at = NOW();

-- Verify the admin was created
SELECT u.id, u.name, u.is_admin, au.email
FROM public.users u
JOIN auth.users au ON u.id = au.id
WHERE au.email = 'harry@cuisto.app';
