-- Migration: 027_add_system_account_and_anonymization
-- Description: Add system account for transferred recipes and support contributor anonymization
-- Date: 2024-12-07

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
-- 3. Create system account in public.users
-- =============================================

-- Note: The auth.users entry must be created via Supabase dashboard or admin API
-- This creates the corresponding public.users entry
-- The system account is used to own transferred recipes (e.g., from deleted users)

INSERT INTO public.users (id, name, date_of_birth, email, profile_completed, onboarding_completed)
VALUES (
    '00000000-0000-0000-0000-000000000000',
    'Cuistudio',
    '2024-01-01',
    'system@cuisto.app',
    true,
    true
)
ON CONFLICT (id) DO NOTHING;


-- =============================================
-- 4. Add index for efficient lookup by display_name
-- =============================================

CREATE INDEX IF NOT EXISTS idx_recipe_contributors_display_name
ON recipe_contributors (display_name)
WHERE display_name IS NOT NULL;
