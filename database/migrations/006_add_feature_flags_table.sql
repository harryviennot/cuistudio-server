-- Migration: 006_add_feature_flags_table
-- Description: Feature flags for gradual rollout and A/B testing of new extraction methods

-- Create feature_flags table
CREATE TABLE IF NOT EXISTS public.feature_flags (
    id uuid DEFAULT extensions.uuid_generate_v4() PRIMARY KEY,
    flag_name VARCHAR(100) NOT NULL UNIQUE,
    enabled BOOLEAN DEFAULT false,
    rollout_percentage INTEGER DEFAULT 0 CHECK (rollout_percentage >= 0 AND rollout_percentage <= 100),
    description TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT now()
);

-- Index for quick lookups by flag name
CREATE INDEX IF NOT EXISTS idx_feature_flags_name
ON public.feature_flags(flag_name);

-- Insert all feature flags (all disabled by default)
INSERT INTO public.feature_flags (flag_name, enabled, rollout_percentage, description) VALUES
    -- Extraction flow flags
    ('dynamic_content_detection', false, 0, 'Use ContentTypeDetector instead of hardcoded is_video_url() patterns'),
    ('slideshow_extraction', false, 0, 'Enable SlideshowExtractor for TikTok/Instagram image carousels'),
    ('vision_api_extraction', false, 0, 'Enable Gemini Vision API for image analysis instead of OCR'),
    ('dynamic_client_download', false, 0, 'Use PlatformStatusService for dynamic client download detection'),
    -- Full Gemini stack flags (AI provider swap)
    ('gemini_3_text_extraction', false, 0, 'Use gemini-3-flash-preview instead of gemini-2.5-flash-lite for text'),
    ('gemini_audio_transcription', false, 0, 'Use Gemini 3 Flash for audio transcription instead of local Whisper'),
    ('gemini_image_generation', false, 0, 'Use Gemini 2.5 Flash Image instead of Flux for image generation')
ON CONFLICT (flag_name) DO NOTHING;

-- Add column comments for documentation
COMMENT ON TABLE public.feature_flags IS 'Feature flags for gradual rollout of new extraction methods and A/B testing';
COMMENT ON COLUMN public.feature_flags.flag_name IS 'Unique identifier for the flag';
COMMENT ON COLUMN public.feature_flags.enabled IS 'Whether the flag is globally enabled';
COMMENT ON COLUMN public.feature_flags.rollout_percentage IS 'Percentage of users/requests to enable for (0-100)';
COMMENT ON COLUMN public.feature_flags.description IS 'Human-readable description of what this flag controls';
