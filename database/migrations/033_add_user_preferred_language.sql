-- Migration: Add preferred_language column to users table
-- Purpose: Store user's language preference for localized notifications

-- Add preferred_language column with default 'en'
ALTER TABLE public.users
ADD COLUMN IF NOT EXISTS preferred_language TEXT DEFAULT 'en';

-- Add comment explaining the column
COMMENT ON COLUMN public.users.preferred_language IS 'User preferred language for notifications (en, fr). Synced from mobile app settings.';

-- Add check constraint for valid language values
-- Using DO block to handle case where constraint already exists
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint
        WHERE conname = 'valid_preferred_language'
    ) THEN
        ALTER TABLE public.users
        ADD CONSTRAINT valid_preferred_language
        CHECK (preferred_language IN ('en', 'fr'));
    END IF;
END $$;

-- Create index for efficient filtering by language (useful for bulk notifications)
CREATE INDEX IF NOT EXISTS idx_users_preferred_language
ON public.users(preferred_language);
