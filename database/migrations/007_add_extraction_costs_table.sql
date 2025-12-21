-- Migration: 007_add_extraction_costs_table
-- Description: Track AI costs per extraction for benchmarking old vs new methods

-- Create extraction_costs table to track all AI API costs
CREATE TABLE IF NOT EXISTS public.extraction_costs (
    id uuid DEFAULT extensions.uuid_generate_v4() PRIMARY KEY,
    extraction_job_id uuid REFERENCES public.extraction_jobs(id) ON DELETE CASCADE,
    service_provider VARCHAR(50) NOT NULL,
    service_type VARCHAR(50) NOT NULL,
    model_name VARCHAR(100),
    input_tokens INTEGER,
    output_tokens INTEGER,
    audio_seconds FLOAT,
    images_processed INTEGER,
    estimated_cost_usd DECIMAL(10, 6),
    processing_time_ms INTEGER,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now()
);

-- Index for looking up costs by job
CREATE INDEX IF NOT EXISTS idx_extraction_costs_job
ON public.extraction_costs(extraction_job_id);

-- Index for aggregating costs by date
CREATE INDEX IF NOT EXISTS idx_extraction_costs_date
ON public.extraction_costs(created_at);

-- Index for filtering by provider/type for benchmarking
CREATE INDEX IF NOT EXISTS idx_extraction_costs_provider_type
ON public.extraction_costs(service_provider, service_type);

-- Add columns to extraction_jobs for tracking content type and method
ALTER TABLE public.extraction_jobs
ADD COLUMN IF NOT EXISTS content_type VARCHAR(30);

ALTER TABLE public.extraction_jobs
ADD COLUMN IF NOT EXISTS extraction_method VARCHAR(50);

-- Add column comments for documentation
COMMENT ON TABLE public.extraction_costs IS 'Tracks AI API costs per extraction for benchmarking and cost monitoring';
COMMENT ON COLUMN public.extraction_costs.service_provider IS 'AI provider: gemini, openai, flux, whisper_local';
COMMENT ON COLUMN public.extraction_costs.service_type IS 'Type of AI call: transcription, text_extraction, vision, image_generation';
COMMENT ON COLUMN public.extraction_costs.model_name IS 'Specific model used (e.g., gemini-3-flash-preview)';
COMMENT ON COLUMN public.extraction_costs.input_tokens IS 'Number of input tokens consumed';
COMMENT ON COLUMN public.extraction_costs.output_tokens IS 'Number of output tokens generated';
COMMENT ON COLUMN public.extraction_costs.audio_seconds IS 'Duration of audio processed (for transcription)';
COMMENT ON COLUMN public.extraction_costs.images_processed IS 'Number of images processed (for vision)';
COMMENT ON COLUMN public.extraction_costs.estimated_cost_usd IS 'Estimated cost in USD';
COMMENT ON COLUMN public.extraction_costs.processing_time_ms IS 'Time taken to process in milliseconds';
COMMENT ON COLUMN public.extraction_jobs.content_type IS 'Detected content type: video, slideshow, image_post, webpage, unknown';
COMMENT ON COLUMN public.extraction_jobs.extraction_method IS 'Extraction method used: video_extractor, slideshow_extractor, vision_api, ocr, webpage_scrape';
