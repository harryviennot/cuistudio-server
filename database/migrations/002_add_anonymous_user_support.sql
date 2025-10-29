-- =============================================
-- ANONYMOUS USER SUPPORT
-- =============================================
-- This migration adds helpful views and comments for anonymous user support.
-- Supabase's auth.users table already has is_anonymous field built-in.
-- No schema changes needed - anonymous users work with existing RLS policies.

-- =============================================
-- HELPER VIEW: User Authentication Status
-- =============================================
-- This view makes it easier to check if users are anonymous or authenticated
-- by joining the public.users table with auth.users

CREATE OR REPLACE VIEW public.user_auth_status AS
SELECT
    u.id,
    u.name,
    u.email,
    u.phone,
    au.is_anonymous,
    au.email as auth_email,
    au.phone as auth_phone,
    au.created_at as auth_created_at,
    u.profile_completed,
    u.created_at as profile_created_at
FROM public.users u
LEFT JOIN auth.users au ON u.id = au.id;

COMMENT ON VIEW public.user_auth_status IS 'Combines user profile data with authentication status including is_anonymous flag';

-- =============================================
-- HELPER FUNCTION: Check if user is anonymous
-- =============================================

CREATE OR REPLACE FUNCTION public.is_user_anonymous(user_id UUID)
RETURNS BOOLEAN
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
DECLARE
    is_anon BOOLEAN;
BEGIN
    SELECT is_anonymous INTO is_anon
    FROM auth.users
    WHERE id = user_id;

    RETURN COALESCE(is_anon, false);
END;
$$;

COMMENT ON FUNCTION public.is_user_anonymous(UUID) IS 'Returns true if the user is anonymous, false otherwise';

-- =============================================
-- RLS POLICY NOTES
-- =============================================
-- Anonymous users work with existing RLS policies because:
-- 1. They have a valid auth.uid() just like authenticated users
-- 2. Existing policies use auth.uid() = id checks which work for both
-- 3. No special policies needed for anonymous users
--
-- Example of how anonymous users interact with existing policies:
--   - "Users can create their own profile" - Works (auth.uid() = id)
--   - "Users can update their own profile" - Works (auth.uid() = id)
--   - "Profiles are viewable by everyone" - Works (true for all)
--
-- If you need to restrict certain operations to authenticated users only,
-- add policies like:
--   USING (auth.uid() = id AND NOT is_user_anonymous(auth.uid()))

-- =============================================
-- COMMENTS FOR DOCUMENTATION
-- =============================================

COMMENT ON COLUMN public.users.profile_completed IS
    'Profile completion status. Anonymous users start as is_new_user=true until they optionally complete profile';

-- =============================================
-- MIGRATION NOTES
-- =============================================
-- This migration is optional and informational.
-- Key points:
-- 1. Supabase auth.users already has is_anonymous field
-- 2. Anonymous users get permanent UUIDs via auth.sign_in_anonymously()
-- 3. When anonymous users link email/phone, same UUID is kept
-- 4. All existing RLS policies work for anonymous users
-- 5. Use get_authenticated_user() dependency in FastAPI to require non-anonymous
