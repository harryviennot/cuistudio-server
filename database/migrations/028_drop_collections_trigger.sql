-- Migration: Drop Collections Trigger and Functions
--
-- Migration 024 dropped the user_collections table but left behind
-- the trigger and functions that reference it. This causes errors
-- when new users sign up:
--   "relation 'user_collections' does not exist" (42P01)
--
-- Collections are now virtual (computed from user_recipe_data fields).

-- Drop the trigger first (depends on the function)
DROP TRIGGER IF EXISTS on_user_created_create_collections ON public.users;

-- Drop the functions
DROP FUNCTION IF EXISTS trigger_create_default_collections();
DROP FUNCTION IF EXISTS create_default_collections(UUID);
DROP FUNCTION IF EXISTS get_user_collection_id(UUID, VARCHAR);
