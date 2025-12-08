-- Migration: Create blog_posts table for content marketing
-- Description: Adds a blog system for SEO content marketing articles.

-- Create blog_posts table
CREATE TABLE IF NOT EXISTS blog_posts (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  slug TEXT UNIQUE NOT NULL,
  title TEXT NOT NULL,
  description TEXT,
  content TEXT NOT NULL,
  featured_image_url TEXT,
  author_name TEXT DEFAULT 'Cuisto Team',
  tags TEXT[] DEFAULT '{}',
  is_published BOOLEAN DEFAULT false,
  published_at TIMESTAMPTZ,
  created_at TIMESTAMPTZ DEFAULT now(),
  updated_at TIMESTAMPTZ DEFAULT now()
);

-- Enable RLS
ALTER TABLE blog_posts ENABLE ROW LEVEL SECURITY;

-- RLS policy: Anyone can read published posts (for public website)
CREATE POLICY "Public can read published posts"
  ON blog_posts FOR SELECT
  USING (is_published = true);

-- Index for fast slug lookups
CREATE INDEX IF NOT EXISTS idx_blog_posts_slug ON blog_posts(slug);

-- Index for listing published posts ordered by date
CREATE INDEX IF NOT EXISTS idx_blog_posts_published ON blog_posts(is_published, published_at DESC);

-- Index for tag filtering
CREATE INDEX IF NOT EXISTS idx_blog_posts_tags ON blog_posts USING GIN(tags);

-- Updated_at trigger (reuse existing function if available)
DO $$
BEGIN
  -- Check if trigger already exists
  IF NOT EXISTS (
    SELECT 1 FROM pg_trigger WHERE tgname = 'set_blog_posts_updated_at'
  ) THEN
    CREATE TRIGGER set_blog_posts_updated_at
      BEFORE UPDATE ON blog_posts
      FOR EACH ROW
      EXECUTE FUNCTION update_updated_at_column();
  END IF;
END $$;

-- Add table comment
COMMENT ON TABLE blog_posts IS 'Blog posts for SEO content marketing. Only published posts are publicly accessible.';

-- Add column comments
COMMENT ON COLUMN blog_posts.slug IS 'URL-friendly unique identifier for the post';
COMMENT ON COLUMN blog_posts.content IS 'Markdown content of the blog post';
COMMENT ON COLUMN blog_posts.is_published IS 'Only published posts are visible on the public website';
COMMENT ON COLUMN blog_posts.published_at IS 'Date when the post was published (can be set in advance for scheduling)';
