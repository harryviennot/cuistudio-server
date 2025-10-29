-- =============================================
-- SUPABASE STORAGE CONFIGURATION FOR RECIPE IMAGES
-- =============================================
-- This migration provides helper functions for recipe image storage.
-- Storage bucket and RLS policies must be configured via Supabase Dashboard.

-- =============================================
-- STORAGE BUCKET SETUP (Manual Steps Required)
-- =============================================
-- STEP 1: Go to Supabase Dashboard → Storage → Create Bucket
--   Bucket Name: recipe-images
--   Public: Yes (to allow public URL access)
--   File Size Limit: 50MB
--   Allowed MIME types: image/jpeg, image/jpg, image/png, image/heic, image/heif, image/webp, image/gif
--
-- STEP 2: Configure Storage Policies via Supabase Dashboard SQL Editor
--   Run the following SQL in the Supabase Dashboard SQL Editor:
--
-- Allow authenticated users to upload recipe images
CREATE POLICY "Users can upload recipe images"
ON storage.objects
  FOR INSERT
  TO authenticated
  WITH CHECK (
      bucket_id = 'recipe-images' AND
      auth.uid()::text = (storage.foldername(name))[1]
  );
--
-- Allow authenticated users to update their own uploaded images
  CREATE POLICY "Users can update their own recipe images"
  ON storage.objects
  FOR UPDATE
  TO authenticated
  USING (
      bucket_id = 'recipe-images' AND
      auth.uid()::text = (storage.foldername(name))[1]
  );
--
-- Allow authenticated users to delete their own uploaded images
  CREATE POLICY "Users can delete their own recipe images"
  ON storage.objects
  FOR DELETE
  TO authenticated
  USING (
      bucket_id = 'recipe-images' AND
      auth.uid()::text = (storage.foldername(name))[1]
  );
--
-- Allow public read access to all recipe images
  CREATE POLICY "Recipe images are publicly readable"
  ON storage.objects
  FOR SELECT
  TO public
  USING (bucket_id = 'recipe-images');

-- =============================================
-- HELPER FUNCTION: Generate Storage Path
-- =============================================
-- Helper function to generate consistent storage paths
-- Format: {user_id}/{uuid}.{extension}
CREATE OR REPLACE FUNCTION public.generate_recipe_image_path(
    user_id UUID,
    file_extension TEXT
)
RETURNS TEXT
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN user_id::text || '/' || gen_random_uuid()::text || '.' || file_extension;
END;
$$;

COMMENT ON FUNCTION public.generate_recipe_image_path(UUID, TEXT) IS
    'Generates a unique storage path for recipe images in format: {user_id}/{uuid}.{extension}';

-- =============================================
-- STORAGE CONFIGURATION NOTES
-- =============================================
-- Path Structure:
--   recipe-images/{user_id}/{uuid}.{extension}
--
-- Example:
--   recipe-images/a1b2c3d4-e5f6-7890-abcd-ef1234567890/img_abc123.jpg
--
-- Public URL Format:
--   https://{project}.supabase.co/storage/v1/object/public/recipe-images/{user_id}/{uuid}.{extension}
--
-- File Naming:
--   - User ID folder ensures users can only access their own uploads
--   - UUID prevents filename conflicts
--   - Extension preserved for proper MIME type handling
--
-- Cleanup Strategy:
--   - Images can be deleted when extraction job is discarded
--   - Or kept permanently if recipe is saved
--   - Consider scheduled cleanup for old unsuccessful extractions
