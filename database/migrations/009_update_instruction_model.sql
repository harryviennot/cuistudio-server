-- =============================================
-- UPDATE INSTRUCTION MODEL
-- =============================================
-- This migration updates the instruction model from having a single "text" field
-- to having separate "title" and "description" fields for better structure.
--
-- Old format: {"step_number": 1, "text": "instruction text", "timer_minutes": 5, "group": "For the soup"}
-- New format: {"step_number": 1, "title": "Step title", "description": "Detailed instruction text", "timer_minutes": 5, "group": "For the soup"}

-- =============================================
-- DATA MIGRATION: Transform existing instructions
-- =============================================

-- Function to migrate a single instruction from old format to new format
CREATE OR REPLACE FUNCTION migrate_instruction(instruction JSONB)
RETURNS JSONB
LANGUAGE plpgsql
IMMUTABLE
AS $$
DECLARE
    text_content TEXT;
    new_instruction JSONB;
BEGIN
    -- Check if instruction already has 'title' field (already migrated)
    IF instruction ? 'title' THEN
        RETURN instruction;
    END IF;

    -- Check if instruction has 'text' field (old format)
    IF NOT instruction ? 'text' THEN
        RETURN instruction;
    END IF;

    -- Extract the text content
    text_content := instruction->>'text';

    -- Migration strategy: use "Title" as title, move text to description
    new_instruction := jsonb_build_object(
        'step_number', instruction->'step_number',
        'title', 'Title',
        'description', text_content,
        'timer_minutes', instruction->'timer_minutes',
        'group', instruction->'group'
    );

    RETURN new_instruction;
END;
$$;

COMMENT ON FUNCTION migrate_instruction(JSONB) IS
    'Migrates a single instruction from old format (with "text") to new format (with "title" and "description")';

-- Function to migrate all instructions in a JSONB array
CREATE OR REPLACE FUNCTION migrate_instructions_array(instructions JSONB)
RETURNS JSONB
LANGUAGE plpgsql
IMMUTABLE
AS $$
DECLARE
    result JSONB := '[]'::jsonb;
    instruction JSONB;
BEGIN
    -- If instructions is not an array, return it as-is
    IF jsonb_typeof(instructions) != 'array' THEN
        RETURN instructions;
    END IF;

    -- Iterate through each instruction and migrate it
    FOR instruction IN SELECT * FROM jsonb_array_elements(instructions)
    LOOP
        result := result || jsonb_build_array(migrate_instruction(instruction));
    END LOOP;

    RETURN result;
END;
$$;

COMMENT ON FUNCTION migrate_instructions_array(JSONB) IS
    'Migrates an array of instructions from old format to new format';

-- =============================================
-- MIGRATE EXISTING RECIPES
-- =============================================

-- Update all recipes to use the new instruction format
UPDATE recipes
SET instructions = migrate_instructions_array(instructions)
WHERE jsonb_typeof(instructions) = 'array'
  AND EXISTS (
    -- Only update if at least one instruction has the old 'text' field
    SELECT 1
    FROM jsonb_array_elements(instructions) AS instruction
    WHERE instruction ? 'text' AND NOT instruction ? 'title'
  );

-- =============================================
-- VALIDATION FUNCTION
-- =============================================

-- Function to validate instruction format
CREATE OR REPLACE FUNCTION validate_instruction_format(instruction JSONB)
RETURNS BOOLEAN
LANGUAGE plpgsql
IMMUTABLE
AS $$
BEGIN
    -- An instruction must have step_number, title, and description
    RETURN (
        instruction ? 'step_number' AND
        instruction ? 'title' AND
        instruction ? 'description'
    );
END;
$$;

COMMENT ON FUNCTION validate_instruction_format(JSONB) IS
    'Validates that an instruction has the required fields: step_number, title, and description';

-- Optional: Add a check constraint to ensure new instructions follow the format
-- Uncomment this if you want to enforce the format at the database level
-- Note: This will prevent inserts/updates that don't follow the new format

-- ALTER TABLE recipes
-- ADD CONSTRAINT check_instructions_format
-- CHECK (
--     jsonb_typeof(instructions) = 'array' AND
--     (
--         SELECT COUNT(*) = 0
--         FROM jsonb_array_elements(instructions) AS instruction
--         WHERE NOT validate_instruction_format(instruction)
--     )
-- );

-- =============================================
-- CLEANUP
-- =============================================

-- Drop the migration helper functions after migration is complete
-- Uncomment these lines after verifying the migration was successful

-- DROP FUNCTION IF EXISTS migrate_instruction(JSONB);
-- DROP FUNCTION IF EXISTS migrate_instructions_array(JSONB);

-- Keep the validation function for future use
-- DROP FUNCTION IF EXISTS validate_instruction_format(JSONB);

-- =============================================
-- VERIFICATION QUERIES
-- =============================================

-- Query to check if any recipes still have the old format:
-- SELECT id, title,
--        jsonb_array_elements(instructions) AS instruction
-- FROM recipes
-- WHERE EXISTS (
--     SELECT 1
--     FROM jsonb_array_elements(instructions) AS inst
--     WHERE inst ? 'text' AND NOT inst ? 'title'
-- );

-- Query to count migrated vs unmigrated recipes:
-- SELECT
--     COUNT(*) FILTER (WHERE EXISTS (
--         SELECT 1 FROM jsonb_array_elements(instructions) AS inst
--         WHERE inst ? 'title'
--     )) AS migrated_recipes,
--     COUNT(*) FILTER (WHERE EXISTS (
--         SELECT 1 FROM jsonb_array_elements(instructions) AS inst
--         WHERE inst ? 'text' AND NOT inst ? 'title'
--     )) AS old_format_recipes,
--     COUNT(*) AS total_recipes
-- FROM recipes
-- WHERE jsonb_typeof(instructions) = 'array';

-- =============================================
-- MIGRATION NOTES
-- =============================================
-- Migration Strategy:
--   - The migration function extracts the "text" field
--   - For the "title": Sets to "Title" (generic placeholder)
--   - For the "description": Uses the full original text from "text" field
--   - Preserves all other fields: step_number, timer_minutes, group
--
-- Backward Compatibility:
--   - The validation function can be used to check format
--   - Optional check constraint can enforce new format
--   - Migration functions can be kept or dropped after migration
--
-- Future Instructions:
--   - New extractions will use the updated OpenAI prompts
--   - They will automatically have title and description
--   - Old recipes are migrated to the new format
