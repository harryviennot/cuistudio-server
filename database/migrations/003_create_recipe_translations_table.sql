-- Migration: Create recipe_translations table
-- Description: Stores cached translations of recipes in different languages.
--              Translations are derived from the original recipe and can be
--              invalidated when the original recipe is edited.

-- Create recipe translations table
CREATE TABLE IF NOT EXISTS public.recipe_translations (
    id UUID DEFAULT extensions.uuid_generate_v4() PRIMARY KEY,
    recipe_id UUID NOT NULL REFERENCES public.recipes(id) ON DELETE CASCADE,
    language VARCHAR(5) NOT NULL,  -- ISO 639-1 language code (en, fr, es, it, de, etc.)
    title VARCHAR(255) NOT NULL,
    description TEXT,
    ingredients JSONB NOT NULL DEFAULT '[]'::jsonb,
    instructions JSONB NOT NULL DEFAULT '[]'::jsonb,
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now(),

    -- One translation per language per recipe
    CONSTRAINT recipe_translations_unique_lang UNIQUE (recipe_id, language)
);

-- Create indexes for efficient lookups
CREATE INDEX IF NOT EXISTS idx_recipe_translations_recipe_id
    ON public.recipe_translations(recipe_id);

CREATE INDEX IF NOT EXISTS idx_recipe_translations_language
    ON public.recipe_translations(language);

CREATE INDEX IF NOT EXISTS idx_recipe_translations_recipe_lang
    ON public.recipe_translations(recipe_id, language);

-- Enable Row Level Security
ALTER TABLE public.recipe_translations ENABLE ROW LEVEL SECURITY;

-- RLS Policy: Anyone can view translations of public recipes or their own recipes
CREATE POLICY "View translations of accessible recipes"
    ON public.recipe_translations FOR SELECT
    USING (EXISTS (
        SELECT 1 FROM public.recipes
        WHERE id = recipe_translations.recipe_id
        AND (is_public = true OR created_by = auth.uid())
    ));

-- RLS Policy: Authenticated users can create translations
CREATE POLICY "Authenticated users can create translations"
    ON public.recipe_translations FOR INSERT
    WITH CHECK (auth.uid() IS NOT NULL);

-- RLS Policy: Users can delete translations of their own recipes
CREATE POLICY "Delete translations of own recipes"
    ON public.recipe_translations FOR DELETE
    USING (EXISTS (
        SELECT 1 FROM public.recipes
        WHERE id = recipe_translations.recipe_id
        AND created_by = auth.uid()
    ));

-- RLS Policy: Users can update translations of their own recipes
CREATE POLICY "Update translations of own recipes"
    ON public.recipe_translations FOR UPDATE
    USING (EXISTS (
        SELECT 1 FROM public.recipes
        WHERE id = recipe_translations.recipe_id
        AND created_by = auth.uid()
    ));

-- Function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_recipe_translation_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = now();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger to auto-update updated_at on modification
DROP TRIGGER IF EXISTS set_recipe_translation_updated_at ON public.recipe_translations;
CREATE TRIGGER set_recipe_translation_updated_at
    BEFORE UPDATE ON public.recipe_translations
    FOR EACH ROW
    EXECUTE FUNCTION update_recipe_translation_updated_at();

-- Add comments for documentation
COMMENT ON TABLE public.recipe_translations IS 'Cached translations of recipes in different languages. Translations are generated via AI and invalidated when the original recipe is edited.';
COMMENT ON COLUMN public.recipe_translations.language IS 'ISO 639-1 language code (e.g., en, fr, es, it, de)';
COMMENT ON COLUMN public.recipe_translations.ingredients IS 'Translated ingredients array with same structure as recipes.ingredients';
COMMENT ON COLUMN public.recipe_translations.instructions IS 'Translated instructions array with same structure as recipes.instructions';
