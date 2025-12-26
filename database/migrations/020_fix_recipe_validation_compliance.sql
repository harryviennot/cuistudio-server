-- Migration: Fix recipe data to comply with new validation rules
--
-- Issues fixed:
-- 1. Trim tags to maximum 10 items (3 recipes affected)
-- 2. Convert string ingredient quantities to null + notes (8 ingredients in 2 recipes)

-- ============================================
-- 1. TAGS: Trim to maximum 10 items
-- ============================================
-- Affected recipes:
-- - High Protein Spicy Grilled Chicken Wraps (15 tags -> 10)
-- - Easy Bulking Chipotle Chicken & Potato Bowls (13 tags -> 10)
-- - Chorizo-Paprika Pasta (12 tags -> 10)

UPDATE recipes
SET
  tags = tags[1:10],
  updated_at = NOW()
WHERE array_length(tags, 1) > 10;

-- ============================================
-- 2. INGREDIENT QUANTITIES: Convert strings to null + notes
-- ============================================
-- Affected ingredients (quantities like "a little bit", "some", "a good glug"):
-- - Potato Breakfast Sandwich Hack: 7 ingredients
-- - Marry Me Butterbeans: 1 ingredient
--
-- Strategy: Move string quantity to notes field, set quantity to null

UPDATE recipes
SET
  ingredients = (
    SELECT jsonb_agg(
      CASE
        WHEN jsonb_typeof(ing->'quantity') = 'string' THEN
          -- Move string quantity to notes, set quantity to null
          jsonb_set(
            jsonb_set(ing, '{quantity}', 'null'),
            '{notes}',
            to_jsonb(
              COALESCE(ing->>'notes', '') ||
              CASE WHEN ing->>'notes' IS NOT NULL AND ing->>'notes' != '' THEN ', ' ELSE '' END ||
              (ing->>'quantity')
            )
          )
        ELSE ing
      END
    )
    FROM jsonb_array_elements(ingredients) as ing
  ),
  updated_at = NOW()
WHERE EXISTS (
  SELECT 1
  FROM jsonb_array_elements(ingredients) as ing
  WHERE jsonb_typeof(ing->'quantity') = 'string'
);

-- Add comments explaining the constraints
COMMENT ON COLUMN recipes.tags IS 'Recipe tags for categorization. Maximum 10 tags allowed.';
COMMENT ON COLUMN recipes.ingredients IS 'Recipe ingredients as JSONB array. quantity must be a number or null.';
