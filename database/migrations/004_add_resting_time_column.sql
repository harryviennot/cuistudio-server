-- Migration: 004_add_resting_time_column
-- Description: Add resting_time_minutes column to recipes and user_recipe_data tables
-- Resting time represents passive waiting periods like marinating, rising dough,
-- freezing, cooling, or resting meat - time that is not active prep or cooking.

-- Add resting_time_minutes to recipes table (base recipe timing)
ALTER TABLE public.recipes
ADD COLUMN IF NOT EXISTS resting_time_minutes INTEGER;

-- Add custom_resting_time_minutes to user_recipe_data table (user customization)
ALTER TABLE public.user_recipe_data
ADD COLUMN IF NOT EXISTS custom_resting_time_minutes INTEGER;

-- Add column comments for documentation
COMMENT ON COLUMN public.recipes.resting_time_minutes IS 'Passive waiting time in minutes (marinating, rising, freezing, cooling, resting). Not active prep or cooking.';
COMMENT ON COLUMN public.user_recipe_data.custom_resting_time_minutes IS 'User custom resting time override in minutes';
