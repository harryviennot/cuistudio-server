-- Migration: Drop category_translations table
-- Date: 2024-12-25
-- Reason: Moving translations to frontend i18n files for instant language switching
--         without API calls. Categories now only contain slug + metadata.

-- Drop the category_translations table
DROP TABLE IF EXISTS public.category_translations CASCADE;

-- Drop the index if it exists (should be removed with CASCADE but being explicit)
DROP INDEX IF EXISTS idx_category_translations_locale;
DROP INDEX IF EXISTS idx_category_translations_category;
