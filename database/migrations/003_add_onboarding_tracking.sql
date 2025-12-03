-- Migration: Add onboarding tracking for new user flow
-- This migration adds a dedicated table for onboarding questionnaire data
-- and a flag to track onboarding completion status

-- Add onboarding_completed field to users table
ALTER TABLE public.users
ADD COLUMN IF NOT EXISTS onboarding_completed BOOLEAN DEFAULT false;

-- Update existing users (assume they've completed onboarding if record exists)
UPDATE public.users SET onboarding_completed = true WHERE id IS NOT NULL;

-- Create user_onboarding table for questionnaire data
CREATE TABLE IF NOT EXISTS public.user_onboarding (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,

  -- Onboarding questionnaire fields (all required except display_name)
  heard_from TEXT NOT NULL, -- 'social_media', 'friend', 'app_store', 'blog', 'search_engine', 'other'
  cooking_frequency TEXT NOT NULL, -- 'rarely', 'occasionally', 'regularly', 'almost_daily'
  recipe_sources TEXT[] NOT NULL, -- array: ['tiktok', 'instagram', 'youtube', 'blogs', 'cookbooks', 'family', 'other']
  display_name TEXT, -- optional user display name

  -- Metadata
  completed_at TIMESTAMPTZ DEFAULT NOW(),
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW(),

  UNIQUE(user_id)
);

-- Enable Row Level Security
ALTER TABLE user_onboarding ENABLE ROW LEVEL SECURITY;

-- RLS Policy: Users can only view their own onboarding data
CREATE POLICY "Users can view own onboarding"
  ON user_onboarding FOR SELECT
  USING (auth.uid() = user_id);

-- RLS Policy: Users can insert their own onboarding data
CREATE POLICY "Users can insert own onboarding"
  ON user_onboarding FOR INSERT
  WITH CHECK (auth.uid() = user_id);

-- RLS Policy: Users can update their own onboarding data
CREATE POLICY "Users can update own onboarding"
  ON user_onboarding FOR UPDATE
  USING (auth.uid() = user_id);

-- Create index for faster lookups
CREATE INDEX IF NOT EXISTS idx_user_onboarding_user_id ON user_onboarding(user_id);

-- Add comment explaining the table purpose
COMMENT ON TABLE user_onboarding IS 'Stores user onboarding questionnaire responses for analytics and personalization';
COMMENT ON COLUMN user_onboarding.heard_from IS 'Marketing source: how user discovered the app';
COMMENT ON COLUMN user_onboarding.cooking_frequency IS 'User cooking habits: rarely, occasionally, regularly, almost_daily';
COMMENT ON COLUMN user_onboarding.recipe_sources IS 'Where user currently gets recipes: tiktok, instagram, youtube, blogs, etc';
COMMENT ON COLUMN user_onboarding.display_name IS 'Optional display name chosen during onboarding';
