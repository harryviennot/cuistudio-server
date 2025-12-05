-- =============================================
-- SUPABASE STORAGE CONFIGURATION FOR COOKING EVENT IMAGES
-- =============================================
-- This migration provides storage policies for cooking session photos.
-- Storage bucket must be configured via Supabase Dashboard first.

-- =============================================
-- STORAGE BUCKET SETUP (Manual Steps Required)
-- =============================================
-- STEP 1: Go to Supabase Dashboard → Storage → Create Bucket
--   Bucket Name: cooking-events
--   Public: Yes (to allow public URL access for viewing photos)
--   File Size Limit: 20MB
--   Allowed MIME types: image/jpeg, image/jpg, image/png, image/heic, image/heif, image/webp
--
-- STEP 2: Run the following SQL in the Supabase Dashboard SQL Editor:

-- Allow authenticated users to upload cooking event images
CREATE POLICY "Users can upload cooking event images"
ON storage.objects
FOR INSERT
TO authenticated
WITH CHECK (
    bucket_id = 'cooking-events' AND
    auth.uid()::text = (storage.foldername(name))[1]
);

-- Allow authenticated users to update their own cooking event images
CREATE POLICY "Users can update their own cooking event images"
ON storage.objects
FOR UPDATE
TO authenticated
USING (
    bucket_id = 'cooking-events' AND
    auth.uid()::text = (storage.foldername(name))[1]
);

-- Allow authenticated users to delete their own cooking event images
CREATE POLICY "Users can delete their own cooking event images"
ON storage.objects
FOR DELETE
TO authenticated
USING (
    bucket_id = 'cooking-events' AND
    auth.uid()::text = (storage.foldername(name))[1]
);

-- Allow public read access to all cooking event images
CREATE POLICY "Cooking event images are publicly readable"
ON storage.objects
FOR SELECT
TO public
USING (bucket_id = 'cooking-events');

-- =============================================
-- HELPER FUNCTION: Generate Storage Path for Cooking Events
-- =============================================
-- Helper function to generate consistent storage paths for cooking photos
-- Format: {user_id}/{event_id}.{extension}
CREATE OR REPLACE FUNCTION public.generate_cooking_event_image_path(
    user_id UUID,
    event_id UUID,
    file_extension TEXT
)
RETURNS TEXT
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN user_id::text || '/' || event_id::text || '.' || file_extension;
END;
$$;

COMMENT ON FUNCTION public.generate_cooking_event_image_path(UUID, UUID, TEXT) IS
    'Generates a unique storage path for cooking event images in format: {user_id}/{event_id}.{extension}';

-- =============================================
-- STORAGE CONFIGURATION NOTES
-- =============================================
-- Path Structure:
--   cooking-events/{user_id}/{event_id}.{extension}
--
-- Example:
--   cooking-events/a1b2c3d4-e5f6-7890-abcd-ef1234567890/f7g8h9i0-j1k2-3456-lmno-pq7890123456.jpg
--
-- Public URL Format:
--   https://{project}.supabase.co/storage/v1/object/public/cooking-events/{user_id}/{event_id}.{extension}
--
-- File Naming:
--   - User ID folder ensures users can only access their own uploads
--   - Event ID links directly to the recipe_cooking_events record
--   - Extension preserved for proper MIME type handling
--
-- Cleanup Strategy:
--   - Consider ON DELETE CASCADE trigger to remove storage objects when events are deleted
--   - Or allow images to persist for historical records
