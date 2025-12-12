-- Migration: Fix recipe_translations INSERT policy
-- Description: Updates the INSERT policy to require that the user can access the recipe
--              (public or owned) before creating a translation. This prevents unauthorized
--              users from creating translations for private recipes.

-- Drop the existing overly permissive policy
DROP POLICY IF EXISTS "Authenticated users can create translations" ON public.recipe_translations;

-- Create a new policy that allows authenticated users to create translations
-- only for recipes they can access (public recipes or their own recipes)
CREATE POLICY "Authenticated users can create translations for accessible recipes"
    ON public.recipe_translations FOR INSERT
    WITH CHECK (
        auth.uid() IS NOT NULL
        AND EXISTS (
            SELECT 1 FROM public.recipes
            WHERE id = recipe_translations.recipe_id
            AND (is_public = true OR created_by = auth.uid())
        )
    );

-- Add comment for documentation
COMMENT ON POLICY "Authenticated users can create translations for accessible recipes"
    ON public.recipe_translations
    IS 'Allows authenticated users to create translations only for recipes they have access to (public or owned)';
