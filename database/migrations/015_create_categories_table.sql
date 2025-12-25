-- Migration: Create categories table for recipe categorization
-- Description: Adds a fixed taxonomy of dish-type categories with i18n support
-- Run this migration BEFORE 016_seed_categories.sql

-- Categories table (includes AI description for dynamic prompt generation)
CREATE TABLE IF NOT EXISTS public.categories (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    slug VARCHAR(50) NOT NULL UNIQUE,
    description TEXT NOT NULL,  -- Used by AI to understand the category
    display_order INTEGER NOT NULL DEFAULT 0,
    icon VARCHAR(50),  -- emoji or icon name for future use
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Category translations table (for i18n - keeps it dynamic)
CREATE TABLE IF NOT EXISTS public.category_translations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    category_id UUID NOT NULL REFERENCES public.categories(id) ON DELETE CASCADE,
    locale VARCHAR(10) NOT NULL,  -- 'en', 'fr', etc.
    name VARCHAR(100) NOT NULL,
    UNIQUE(category_id, locale)
);

-- Add category_id to recipes (foreign key, optional during migration period)
ALTER TABLE public.recipes
ADD COLUMN IF NOT EXISTS category_id UUID REFERENCES public.categories(id);

-- Indexes for fast lookups
CREATE INDEX IF NOT EXISTS idx_recipes_category_id ON public.recipes(category_id);
CREATE INDEX IF NOT EXISTS idx_category_translations_lookup ON public.category_translations(category_id, locale);
CREATE INDEX IF NOT EXISTS idx_categories_slug ON public.categories(slug);
CREATE INDEX IF NOT EXISTS idx_categories_display_order ON public.categories(display_order);

-- Enable RLS on categories (public read, no write from client)
ALTER TABLE public.categories ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.category_translations ENABLE ROW LEVEL SECURITY;

-- RLS policies: Anyone can read categories (they're public reference data)
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_policies WHERE tablename = 'categories' AND policyname = 'Anyone can read categories'
    ) THEN
        CREATE POLICY "Anyone can read categories"
            ON public.categories FOR SELECT
            USING (true);
    END IF;
END $$;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_policies WHERE tablename = 'category_translations' AND policyname = 'Anyone can read category translations'
    ) THEN
        CREATE POLICY "Anyone can read category translations"
            ON public.category_translations FOR SELECT
            USING (true);
    END IF;
END $$;

-- Add table comments
COMMENT ON TABLE public.categories IS 'Fixed taxonomy of dish-type categories. Categories are managed via migrations, not user input.';
COMMENT ON COLUMN public.categories.slug IS 'URL-friendly unique identifier (e.g., soups, desserts)';
COMMENT ON COLUMN public.categories.description IS 'AI-readable description used to build normalization prompts dynamically';
COMMENT ON COLUMN public.categories.display_order IS 'Sort order for category lists in UI';
COMMENT ON COLUMN public.categories.icon IS 'Optional emoji or icon identifier for UI display';

COMMENT ON TABLE public.category_translations IS 'Localized names for categories. Enables dynamic i18n without frontend deploys.';
COMMENT ON COLUMN public.category_translations.locale IS 'ISO 639-1 language code (en, fr, es, etc.)';
COMMENT ON COLUMN public.category_translations.name IS 'Localized display name for the category';

COMMENT ON COLUMN public.recipes.category_id IS 'Foreign key to categories table. Required for new recipes, being backfilled for existing ones.';
