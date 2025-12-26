-- Migration: Drop deprecated categories string array column
-- Date: 2024-12-25
-- Reason: Category information now stored via category_id foreign key
--         Old string array column is no longer needed

-- Drop the deprecated categories column
ALTER TABLE public.recipes DROP COLUMN IF EXISTS categories;
