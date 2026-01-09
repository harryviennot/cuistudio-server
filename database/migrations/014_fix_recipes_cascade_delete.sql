-- Migration: 014_fix_recipes_cascade_delete
-- Description: Add permissive DELETE policy on recipes table to allow CASCADE deletes
-- The existing policy "Users can delete their own recipes" requires auth.uid() = created_by
-- But during CASCADE delete from auth.users, auth.uid() is NULL, blocking the deletion

-- Add a permissive policy that allows cascade deletes
-- Since RLS uses OR logic for permissive policies, this will allow the delete to proceed
CREATE POLICY "Allow cascade delete on recipes"
    ON public.recipes FOR DELETE
    USING (true);
