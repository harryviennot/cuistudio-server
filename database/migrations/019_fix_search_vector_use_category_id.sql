-- Migration: Fix search vector trigger to use category_id instead of deprecated categories array
-- Date: 2024-12-26
-- Reason: The recipes_search_vector_update function was referencing NEW.categories which no longer exists
--         Now it uses category_id to look up the category slug from the categories table

-- Update the search vector trigger function to use category_id instead of deprecated categories array
CREATE OR REPLACE FUNCTION public.recipes_search_vector_update()
RETURNS trigger
LANGUAGE plpgsql
AS $$
DECLARE
  ingredients_text text;
  instructions_text text;
  category_slug text;
  lang_config regconfig;
BEGIN
  -- Extract text from JSONB ingredients array
  SELECT string_agg(item->>'name', ' ')
  INTO ingredients_text
  FROM jsonb_array_elements(NEW.ingredients) AS item;

  -- Extract text from JSONB instructions array
  SELECT string_agg(item->>'text', ' ')
  INTO instructions_text
  FROM jsonb_array_elements(NEW.instructions) AS item;

  -- Get category slug from categories table if category_id is set
  IF NEW.category_id IS NOT NULL THEN
    SELECT slug INTO category_slug
    FROM public.categories
    WHERE id = NEW.category_id;
  END IF;

  -- Select language-specific dictionary for better stemming and stop word removal
  lang_config := CASE
    WHEN NEW.language = 'fr' THEN 'french'::regconfig
    WHEN NEW.language = 'en' THEN 'english'::regconfig
    ELSE 'simple'::regconfig
  END;

  -- Build the search vector with weighted components
  NEW.search_vector :=
    setweight(to_tsvector(lang_config, coalesce(NEW.title, '')), 'A') ||
    setweight(to_tsvector(lang_config, coalesce(array_to_string(NEW.tags, ' '), '')), 'B') ||
    setweight(to_tsvector(lang_config, coalesce(category_slug, '')), 'B') ||
    setweight(to_tsvector(lang_config, coalesce(NEW.description, '')), 'C') ||
    setweight(to_tsvector(lang_config, coalesce(ingredients_text, '')), 'D') ||
    setweight(to_tsvector(lang_config, coalesce(instructions_text, '')), 'D');

  RETURN NEW;
END;
$$;
