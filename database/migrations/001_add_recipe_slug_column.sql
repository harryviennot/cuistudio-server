-- Migration: Add slug column for SEO-friendly recipe URLs
-- Description: Adds a slug column to recipes table for human-readable URLs,
--              with auto-generation triggers and backfill for existing recipes.

-- Add slug column
ALTER TABLE recipes ADD COLUMN IF NOT EXISTS slug TEXT;

-- Create unique index (only for non-null slugs to allow multiple NULL values)
CREATE UNIQUE INDEX IF NOT EXISTS recipes_slug_unique ON recipes(slug) WHERE slug IS NOT NULL;

-- Create index for fast slug lookups
CREATE INDEX IF NOT EXISTS idx_recipes_slug ON recipes(slug) WHERE slug IS NOT NULL;

-- Function to generate slug from title
CREATE OR REPLACE FUNCTION generate_recipe_slug()
RETURNS TRIGGER AS $$
DECLARE
  base_slug TEXT;
  final_slug TEXT;
BEGIN
  -- Only generate if slug is null and recipe is public and not draft
  IF NEW.slug IS NULL AND NEW.is_public = true AND NEW.is_draft = false THEN
    -- Create base slug from title: lowercase, replace non-alphanumeric with hyphens
    base_slug := LOWER(REGEXP_REPLACE(
      REGEXP_REPLACE(NEW.title, '[^a-zA-Z0-9 ]', '', 'g'),
      ' +', '-', 'g'
    ));
    -- Truncate to 60 chars and add short UUID suffix for uniqueness
    base_slug := SUBSTRING(base_slug, 1, 60);
    final_slug := base_slug || '-' || SUBSTRING(NEW.id::text, 1, 6);
    NEW.slug := final_slug;
  END IF;
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger to auto-generate slugs on insert
DROP TRIGGER IF EXISTS set_recipe_slug ON recipes;
CREATE TRIGGER set_recipe_slug
  BEFORE INSERT ON recipes
  FOR EACH ROW
  EXECUTE FUNCTION generate_recipe_slug();

-- Function to generate slug when recipe becomes public
CREATE OR REPLACE FUNCTION update_recipe_slug_on_publish()
RETURNS TRIGGER AS $$
DECLARE
  base_slug TEXT;
  final_slug TEXT;
BEGIN
  -- Generate slug when recipe becomes public and non-draft (and doesn't have one)
  IF NEW.slug IS NULL
     AND NEW.is_public = true
     AND NEW.is_draft = false
     AND (OLD.is_public = false OR OLD.is_draft = true) THEN
    base_slug := LOWER(REGEXP_REPLACE(
      REGEXP_REPLACE(NEW.title, '[^a-zA-Z0-9 ]', '', 'g'),
      ' +', '-', 'g'
    ));
    base_slug := SUBSTRING(base_slug, 1, 60);
    final_slug := base_slug || '-' || SUBSTRING(NEW.id::text, 1, 6);
    NEW.slug := final_slug;
  END IF;
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger to generate slug when recipe is published
DROP TRIGGER IF EXISTS update_recipe_slug_on_publish ON recipes;
CREATE TRIGGER update_recipe_slug_on_publish
  BEFORE UPDATE ON recipes
  FOR EACH ROW
  EXECUTE FUNCTION update_recipe_slug_on_publish();

-- Backfill existing public recipes with slugs
UPDATE recipes SET slug =
  LOWER(REGEXP_REPLACE(
    REGEXP_REPLACE(title, '[^a-zA-Z0-9 ]', '', 'g'),
    ' +', '-', 'g'
  )) || '-' || SUBSTRING(id::text, 1, 6)
WHERE slug IS NULL AND is_public = true AND is_draft = false;

-- Add comment to column
COMMENT ON COLUMN recipes.slug IS 'SEO-friendly URL slug. Auto-generated from title + short UUID when recipe becomes public.';
