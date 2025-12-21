-- Migration: 005_add_platform_status_table
-- Description: Track platform extraction requirements and failure patterns
-- for dynamic client-download detection

-- Create platform_status table to track which platforms require client-side download
CREATE TABLE IF NOT EXISTS public.platform_status (
    id uuid DEFAULT extensions.uuid_generate_v4() PRIMARY KEY,
    platform_domain VARCHAR(255) NOT NULL UNIQUE,
    requires_client_download BOOLEAN DEFAULT false,
    failure_count INTEGER DEFAULT 0,
    last_failure_at TIMESTAMP WITH TIME ZONE,
    last_success_at TIMESTAMP WITH TIME ZONE,
    failure_reason VARCHAR(100),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT now()
);

-- Index for quick lookups by domain
CREATE INDEX IF NOT EXISTS idx_platform_status_domain
ON public.platform_status(platform_domain);

-- Index for finding platforms that need client download
CREATE INDEX IF NOT EXISTS idx_platform_status_client_download
ON public.platform_status(requires_client_download)
WHERE requires_client_download = true;

-- Seed with known problematic platforms
INSERT INTO public.platform_status (platform_domain, requires_client_download, failure_reason)
VALUES
    ('instagram.com', true, 'auth_required'),
    ('facebook.com', true, 'auth_required')
ON CONFLICT (platform_domain) DO NOTHING;

-- Add column comments for documentation
COMMENT ON TABLE public.platform_status IS 'Tracks platform extraction requirements and failure patterns for dynamic client-download detection';
COMMENT ON COLUMN public.platform_status.platform_domain IS 'Normalized domain (e.g., instagram.com, tiktok.com)';
COMMENT ON COLUMN public.platform_status.requires_client_download IS 'Whether this platform requires client-side video download';
COMMENT ON COLUMN public.platform_status.failure_count IS 'Number of consecutive extraction failures';
COMMENT ON COLUMN public.platform_status.failure_reason IS 'Last failure reason (auth_required, rate_limited, blocked, etc.)';
