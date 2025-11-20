-- Migration: Add language-aware full-text search capabilities to recipes
-- Created: 2025-01-30
-- Description: Adds language column, tsvector column, GIN index, and trigger for automatic search vector updates
-- This enables fast, PostgreSQL-native full-text search with language-specific dictionaries
-- for better stemming and stop word removal in English and French

-- Add language column to recipes table
-- Stores ISO 639-1 language code (en, fr, etc.)
ALTER TABLE recipes
ADD COLUMN IF NOT EXISTS language VARCHAR(2) DEFAULT 'en';

-- Add search vector column to recipes table
-- tsvector is PostgreSQL's data type for full-text search documents
ALTER TABLE recipes
ADD COLUMN IF NOT EXISTS search_vector tsvector;

-- Create function to update search vector with language-aware dictionaries
-- This function generates a search document by combining multiple fields with weights:
-- A weight (highest): title - most important for relevance
-- B weight (high): tags, categories - important for filtering
-- C weight (medium): description - contextual information
-- D weight (low): ingredients, instructions - detailed content
CREATE OR REPLACE FUNCTION recipes_search_vector_update() RETURNS trigger AS $$
DECLARE
  ingredients_text text;
  instructions_text text;
  lang_config regconfig;
BEGIN
  -- Extract text from JSONB ingredients array
  -- Each ingredient has a 'name' field we want to search
  SELECT string_agg(item->>'name', ' ')
  INTO ingredients_text
  FROM jsonb_array_elements(NEW.ingredients) AS item;

  -- Extract text from JSONB instructions array
  -- Each instruction has a 'text' field we want to search
  SELECT string_agg(item->>'text', ' ')
  INTO instructions_text
  FROM jsonb_array_elements(NEW.instructions) AS item;

  -- Select language-specific dictionary for better stemming and stop word removal
  -- French: handles "poulet/poulets", "grillé/griller/grillée", removes "le/la/les/de/du"
  -- English: handles "cook/cooking/cooked", "chicken/chickens", removes "the/a/an/with"
  -- Simple: fallback for unknown languages - basic tokenization, no stemming
  lang_config := CASE
    WHEN NEW.language = 'fr' THEN 'french'::regconfig
    WHEN NEW.language = 'en' THEN 'english'::regconfig
    ELSE 'simple'::regconfig
  END;

  -- Build the search vector with weighted components using language-specific dictionary
  -- setweight() assigns importance levels (A=highest, D=lowest)
  -- to_tsvector() converts text to searchable tokens with stemming
  -- coalesce() handles NULL values
  NEW.search_vector :=
    -- Title: highest weight (A) - users often search by dish name
    setweight(to_tsvector(lang_config, coalesce(NEW.title, '')), 'A') ||
    -- Tags: high weight (B) - important categorical information
    setweight(to_tsvector(lang_config, coalesce(array_to_string(NEW.tags, ' '), '')), 'B') ||
    -- Categories: high weight (B) - important categorical information
    setweight(to_tsvector(lang_config, coalesce(array_to_string(NEW.categories, ' '), '')), 'B') ||
    -- Description: medium weight (C) - helpful context
    setweight(to_tsvector(lang_config, coalesce(NEW.description, '')), 'C') ||
    -- Ingredients: low weight (D) - detailed information
    setweight(to_tsvector(lang_config, coalesce(ingredients_text, '')), 'D') ||
    -- Instructions: low weight (D) - detailed information
    setweight(to_tsvector(lang_config, coalesce(instructions_text, '')), 'D');

  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create trigger to automatically update search vector on INSERT or UPDATE
-- This ensures the search index stays in sync with recipe data
DROP TRIGGER IF EXISTS recipes_search_vector_trigger ON recipes;
CREATE TRIGGER recipes_search_vector_trigger
BEFORE INSERT OR UPDATE ON recipes
FOR EACH ROW
EXECUTE FUNCTION recipes_search_vector_update();

-- Create GIN index for fast full-text search queries
-- GIN (Generalized Inverted Index) is optimal for tsvector columns
-- This dramatically speeds up text search queries from O(n) to O(log n)
CREATE INDEX IF NOT EXISTS idx_recipes_search_vector
ON recipes USING GIN (search_vector);

-- Backfill search vectors for existing recipes
-- This updates all existing recipes to populate their search vectors
-- Trigger will fire and populate search_vector based on existing data
UPDATE recipes SET updated_at = updated_at WHERE search_vector IS NULL;

-- Comments for documentation
COMMENT ON COLUMN recipes.language IS
'ISO 639-1 language code (en, fr, etc.) used to select appropriate full-text search dictionary for stemming';

COMMENT ON COLUMN recipes.search_vector IS
'Language-aware full-text search vector combining title, description, ingredients, instructions, tags, and categories with relevance weights';

COMMENT ON INDEX idx_recipes_search_vector IS
'GIN index for fast full-text search queries on recipes. Enables efficient language-aware searches across all recipe content.';

COMMENT ON FUNCTION recipes_search_vector_update() IS
'Trigger function that automatically updates search vector when recipe is created or modified. Uses language-specific dictionaries (french/english/simple) for optimal stemming and stop word removal.';
