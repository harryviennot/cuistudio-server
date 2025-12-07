-- Migration: 027_add_contributor_anonymization
-- Description: Support contributor anonymization for deleted users
-- Date: 2024-12-07
-- Applied via Supabase MCP

-- =============================================
-- 1. Add display_name column for anonymization
-- =============================================

-- Add display_name column to recipe_contributors
-- This stores the display name for deleted users ("[Deleted User]")
ALTER TABLE recipe_contributors
ADD COLUMN IF NOT EXISTS display_name VARCHAR(100) DEFAULT NULL;

COMMENT ON COLUMN recipe_contributors.display_name IS
'Display name for deleted users. When a user deletes their account, this stores "[Deleted User]" and user_id is set to NULL.';


-- =============================================
-- 2. Modify user_id constraint to allow NULL
-- =============================================

-- Drop the existing foreign key constraint
ALTER TABLE recipe_contributors
DROP CONSTRAINT IF EXISTS recipe_contributors_user_id_fkey;

-- Make user_id nullable
ALTER TABLE recipe_contributors
ALTER COLUMN user_id DROP NOT NULL;

-- Re-add the foreign key with ON DELETE SET NULL
ALTER TABLE recipe_contributors
ADD CONSTRAINT recipe_contributors_user_id_fkey
FOREIGN KEY (user_id) REFERENCES auth.users(id) ON DELETE SET NULL;

-- Update the unique constraint to handle NULL user_id
ALTER TABLE recipe_contributors
DROP CONSTRAINT IF EXISTS recipe_contributors_recipe_id_user_id_order_key;

-- Note: With NULL user_id, uniqueness is handled differently
-- Each recipe can have multiple anonymous contributors at different orders
CREATE UNIQUE INDEX IF NOT EXISTS idx_recipe_contributors_unique
ON recipe_contributors (recipe_id, COALESCE(user_id, '00000000-0000-0000-0000-000000000000'::uuid), "order");


-- =============================================
-- 3. Add index for efficient lookup by display_name
-- =============================================

CREATE INDEX IF NOT EXISTS idx_recipe_contributors_display_name
ON recipe_contributors (display_name)
WHERE display_name IS NOT NULL;


-- =============================================
-- NOTE: System Account Creation
-- =============================================
-- The system account (00000000-0000-0000-0000-000000000000) requires:
-- 1. First create entry in auth.users via Supabase Admin API or Dashboard
-- 2. Then create corresponding public.users entry
--
-- This cannot be done via migration because public.users has FK to auth.users.
--
-- For now, video-extracted recipes transfer works without system account:
-- - The backend code sets created_by = SYSTEM_ACCOUNT_ID
-- - This will fail FK constraint until system account exists
-- - Alternative: Keep recipes with deleted user or use NULL
--
-- To create system account manually:
-- 1. Use Supabase Dashboard > Authentication > Users > Create User
-- 2. Set id = 00000000-0000-0000-0000-000000000000
-- 3. Then run:
--    INSERT INTO public.users (id, name, profile_completed, onboarding_completed)
--    VALUES ('00000000-0000-0000-0000-000000000000', 'Cuistudio', true, true)
--    ON CONFLICT (id) DO NOTHING;
