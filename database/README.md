# Database Setup

This directory contains the database schema for the Recipe App using Supabase.

## Setup Instructions

### 1. Create a Supabase Project

1. Go to [supabase.com](https://supabase.com) and create a new project
2. Wait for the project to be provisioned
3. Note down your project URL and anon key

### 2. Run the Schema

1. Open the Supabase SQL Editor (from your project dashboard)
2. Copy the contents of `schema.sql`
3. Paste and execute in the SQL Editor
4. Verify that all tables were created successfully

### 3. Enable Storage (for Images)

1. Go to Storage in your Supabase dashboard
2. Create a new bucket called `recipe-images`
3. Set the bucket to **public** (or configure appropriate policies)
4. Create a policy to allow authenticated users to upload:

```sql
-- Policy for uploading images
CREATE POLICY "Authenticated users can upload images"
ON storage.objects FOR INSERT
TO authenticated
WITH CHECK (bucket_id = 'recipe-images');

-- Policy for viewing images
CREATE POLICY "Anyone can view images"
ON storage.objects FOR SELECT
TO public
USING (bucket_id = 'recipe-images');

-- Policy for deleting own images
CREATE POLICY "Users can delete their own images"
ON storage.objects FOR DELETE
TO authenticated
USING (bucket_id = 'recipe-images' AND auth.uid()::text = (storage.foldername(name))[1]);
```

### 4. Update Environment Variables

Copy `.env.example` to `.env` and fill in your Supabase credentials:

```bash
SUPABASE_URL=your_supabase_project_url
SUPABASE_PUBLISHABLE_KEY=your_supabase_publishable_key
SUPABASE_SECRET_KEY=your_supabase_secret_key
```

## Database Structure

### Core Tables

- **recipes**: Main recipe data
- **recipe_contributors**: Tracks the fork chain and contributors
- **user_recipe_data**: User-specific customizations (ratings, notes, etc.)
- **cookbooks**: Recipe collections
- **cookbook_folders**: Nested folder structure within cookbooks
- **cookbook_recipes**: Recipes in cookbooks
- **folder_recipes**: Recipes in specific folders
- **recipe_shares**: Recipe sharing with specific users
- **cookbook_shares**: Cookbook sharing with specific users
- **featured_recipes**: Featured recipes for homepage
- **extraction_jobs**: Track recipe extraction jobs

### Security

- Row Level Security (RLS) is enabled on all tables
- Policies enforce:
  - Users can only modify their own data
  - Public recipes are viewable by everyone
  - Private recipes are only viewable by owner and shared users
  - Collaborators with appropriate permissions can edit shared recipes

### Indexes

Optimized indexes for:
- User lookups
- Recipe searches
- Full-text search on titles and descriptions
- Tag and category filtering
- Date-based queries

## Migrations

For future schema changes, create migration files in this directory:
- `001_initial_schema.sql` (current schema.sql)
- `002_add_feature_x.sql`
- etc.
