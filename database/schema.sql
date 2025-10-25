-- =============================================
-- Recipe App Database Schema for Supabase
-- =============================================

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- =============================================
-- RECIPES TABLE
-- =============================================
CREATE TABLE recipes (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    title VARCHAR(200) NOT NULL,
    description TEXT,
    image_url TEXT,

    -- Recipe content (stored as JSONB for flexibility)
    ingredients JSONB NOT NULL DEFAULT '[]'::jsonb,
    instructions JSONB NOT NULL DEFAULT '[]'::jsonb,

    -- Metadata
    servings INTEGER CHECK (servings > 0),
    difficulty VARCHAR(20) CHECK (difficulty IN ('easy', 'medium', 'hard')),
    tags TEXT[] DEFAULT ARRAY[]::TEXT[],
    categories TEXT[] DEFAULT ARRAY[]::TEXT[],

    -- Timings
    prep_time_minutes INTEGER,
    cook_time_minutes INTEGER,
    total_time_minutes INTEGER,

    -- Source information
    source_type VARCHAR(20) NOT NULL CHECK (source_type IN ('video', 'photo', 'voice', 'url', 'paste')),
    source_url TEXT,

    -- Attribution & forking
    created_by UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    original_recipe_id UUID REFERENCES recipes(id) ON DELETE SET NULL,
    fork_count INTEGER DEFAULT 0,

    -- Privacy
    is_public BOOLEAN DEFAULT true,

    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes for recipes
CREATE INDEX idx_recipes_created_by ON recipes(created_by);
CREATE INDEX idx_recipes_original_recipe_id ON recipes(original_recipe_id);
CREATE INDEX idx_recipes_is_public ON recipes(is_public);
CREATE INDEX idx_recipes_created_at ON recipes(created_at DESC);
CREATE INDEX idx_recipes_tags ON recipes USING GIN(tags);
CREATE INDEX idx_recipes_categories ON recipes USING GIN(categories);

-- Full-text search index
CREATE INDEX idx_recipes_title_search ON recipes USING GIN(to_tsvector('english', title));
CREATE INDEX idx_recipes_description_search ON recipes USING GIN(to_tsvector('english', COALESCE(description, '')));

-- =============================================
-- RECIPE CONTRIBUTORS TABLE
-- =============================================
CREATE TABLE recipe_contributors (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    recipe_id UUID NOT NULL REFERENCES recipes(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    contribution_type VARCHAR(20) NOT NULL CHECK (contribution_type IN ('creator', 'fork', 'edit')),
    "order" INTEGER NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    UNIQUE(recipe_id, user_id, "order")
);

CREATE INDEX idx_recipe_contributors_recipe_id ON recipe_contributors(recipe_id);
CREATE INDEX idx_recipe_contributors_user_id ON recipe_contributors(user_id);

-- =============================================
-- USER RECIPE DATA TABLE
-- =============================================
CREATE TABLE user_recipe_data (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    recipe_id UUID NOT NULL REFERENCES recipes(id) ON DELETE CASCADE,

    -- Custom ratings and timings
    rating INTEGER CHECK (rating >= 1 AND rating <= 5),
    custom_prep_time_minutes INTEGER,
    custom_cook_time_minutes INTEGER,
    custom_difficulty VARCHAR(20) CHECK (custom_difficulty IN ('easy', 'medium', 'hard')),

    -- Personal notes
    notes TEXT,
    custom_servings INTEGER,

    -- Tracking
    times_cooked INTEGER DEFAULT 0,
    last_cooked_at TIMESTAMP WITH TIME ZONE,
    is_favorite BOOLEAN DEFAULT false,

    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    UNIQUE(user_id, recipe_id)
);

CREATE INDEX idx_user_recipe_data_user_id ON user_recipe_data(user_id);
CREATE INDEX idx_user_recipe_data_recipe_id ON user_recipe_data(recipe_id);
CREATE INDEX idx_user_recipe_data_is_favorite ON user_recipe_data(is_favorite);

-- =============================================
-- COOKBOOKS TABLE
-- =============================================
CREATE TABLE cookbooks (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    title VARCHAR(200) NOT NULL,
    subtitle VARCHAR(500),
    description TEXT,
    image_url TEXT,

    -- Privacy
    is_public BOOLEAN DEFAULT false,

    -- Metadata
    recipe_count INTEGER DEFAULT 0,

    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_cookbooks_user_id ON cookbooks(user_id);
CREATE INDEX idx_cookbooks_is_public ON cookbooks(is_public);

-- =============================================
-- COOKBOOK FOLDERS TABLE
-- =============================================
CREATE TABLE cookbook_folders (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    cookbook_id UUID NOT NULL REFERENCES cookbooks(id) ON DELETE CASCADE,
    parent_folder_id UUID REFERENCES cookbook_folders(id) ON DELETE CASCADE,
    name VARCHAR(100) NOT NULL,
    "order" INTEGER DEFAULT 0,

    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_cookbook_folders_cookbook_id ON cookbook_folders(cookbook_id);
CREATE INDEX idx_cookbook_folders_parent_folder_id ON cookbook_folders(parent_folder_id);

-- =============================================
-- COOKBOOK RECIPES TABLE
-- =============================================
CREATE TABLE cookbook_recipes (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    cookbook_id UUID NOT NULL REFERENCES cookbooks(id) ON DELETE CASCADE,
    recipe_id UUID NOT NULL REFERENCES recipes(id) ON DELETE CASCADE,
    "order" INTEGER DEFAULT 0,
    added_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    UNIQUE(cookbook_id, recipe_id)
);

CREATE INDEX idx_cookbook_recipes_cookbook_id ON cookbook_recipes(cookbook_id);
CREATE INDEX idx_cookbook_recipes_recipe_id ON cookbook_recipes(recipe_id);

-- =============================================
-- FOLDER RECIPES TABLE
-- =============================================
CREATE TABLE folder_recipes (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    folder_id UUID NOT NULL REFERENCES cookbook_folders(id) ON DELETE CASCADE,
    recipe_id UUID NOT NULL REFERENCES recipes(id) ON DELETE CASCADE,
    "order" INTEGER DEFAULT 0,
    added_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    UNIQUE(folder_id, recipe_id)
);

CREATE INDEX idx_folder_recipes_folder_id ON folder_recipes(folder_id);
CREATE INDEX idx_folder_recipes_recipe_id ON folder_recipes(recipe_id);

-- =============================================
-- RECIPE SHARES TABLE
-- =============================================
CREATE TABLE recipe_shares (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    recipe_id UUID NOT NULL REFERENCES recipes(id) ON DELETE CASCADE,
    shared_by_user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    shared_with_user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    permission_level VARCHAR(20) NOT NULL CHECK (permission_level IN ('view', 'fork', 'collaborate')),

    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    UNIQUE(recipe_id, shared_with_user_id)
);

CREATE INDEX idx_recipe_shares_recipe_id ON recipe_shares(recipe_id);
CREATE INDEX idx_recipe_shares_shared_with_user_id ON recipe_shares(shared_with_user_id);

-- =============================================
-- COOKBOOK SHARES TABLE
-- =============================================
CREATE TABLE cookbook_shares (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    cookbook_id UUID NOT NULL REFERENCES cookbooks(id) ON DELETE CASCADE,
    shared_by_user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    shared_with_user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    permission_level VARCHAR(20) NOT NULL CHECK (permission_level IN ('view', 'fork', 'collaborate')),

    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    UNIQUE(cookbook_id, shared_with_user_id)
);

CREATE INDEX idx_cookbook_shares_cookbook_id ON cookbook_shares(cookbook_id);
CREATE INDEX idx_cookbook_shares_shared_with_user_id ON cookbook_shares(shared_with_user_id);

-- =============================================
-- FEATURED RECIPES TABLE
-- =============================================
CREATE TABLE featured_recipes (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    recipe_id UUID NOT NULL REFERENCES recipes(id) ON DELETE CASCADE,
    featured_type VARCHAR(20) NOT NULL CHECK (featured_type IN ('manual', 'trending', 'popular', 'time_of_day')),
    priority INTEGER DEFAULT 0,
    start_date TIMESTAMP WITH TIME ZONE,
    end_date TIMESTAMP WITH TIME ZONE,

    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_featured_recipes_recipe_id ON featured_recipes(recipe_id);
CREATE INDEX idx_featured_recipes_type ON featured_recipes(featured_type);
CREATE INDEX idx_featured_recipes_dates ON featured_recipes(start_date, end_date);

-- =============================================
-- EXTRACTION JOBS TABLE
-- =============================================
CREATE TABLE extraction_jobs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    source_type VARCHAR(20) NOT NULL CHECK (source_type IN ('video', 'photo', 'voice', 'url', 'paste')),
    source_url TEXT,
    status VARCHAR(20) NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'processing', 'completed', 'failed')),

    -- Results
    recipe_id UUID REFERENCES recipes(id) ON DELETE SET NULL,
    error_message TEXT,

    -- Progress tracking
    progress_percentage INTEGER DEFAULT 0,
    current_step VARCHAR(200),

    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_extraction_jobs_user_id ON extraction_jobs(user_id);
CREATE INDEX idx_extraction_jobs_status ON extraction_jobs(status);

-- =============================================
-- TRIGGERS FOR UPDATED_AT
-- =============================================

-- Function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Apply trigger to tables with updated_at
CREATE TRIGGER update_recipes_updated_at BEFORE UPDATE ON recipes
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_user_recipe_data_updated_at BEFORE UPDATE ON user_recipe_data
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_cookbooks_updated_at BEFORE UPDATE ON cookbooks
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_extraction_jobs_updated_at BEFORE UPDATE ON extraction_jobs
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- =============================================
-- ROW LEVEL SECURITY (RLS) POLICIES
-- =============================================

-- Enable RLS on all tables
ALTER TABLE recipes ENABLE ROW LEVEL SECURITY;
ALTER TABLE recipe_contributors ENABLE ROW LEVEL SECURITY;
ALTER TABLE user_recipe_data ENABLE ROW LEVEL SECURITY;
ALTER TABLE cookbooks ENABLE ROW LEVEL SECURITY;
ALTER TABLE cookbook_folders ENABLE ROW LEVEL SECURITY;
ALTER TABLE cookbook_recipes ENABLE ROW LEVEL SECURITY;
ALTER TABLE folder_recipes ENABLE ROW LEVEL SECURITY;
ALTER TABLE recipe_shares ENABLE ROW LEVEL SECURITY;
ALTER TABLE cookbook_shares ENABLE ROW LEVEL SECURITY;
ALTER TABLE featured_recipes ENABLE ROW LEVEL SECURITY;
ALTER TABLE extraction_jobs ENABLE ROW LEVEL SECURITY;

-- Recipes policies
CREATE POLICY "Public recipes are viewable by everyone" ON recipes
    FOR SELECT USING (is_public = true);

CREATE POLICY "Users can view their own recipes" ON recipes
    FOR SELECT USING (auth.uid() = created_by);

CREATE POLICY "Users can view shared recipes" ON recipes
    FOR SELECT USING (
        EXISTS (
            SELECT 1 FROM recipe_shares
            WHERE recipe_shares.recipe_id = recipes.id
            AND recipe_shares.shared_with_user_id = auth.uid()
        )
    );

CREATE POLICY "Users can insert their own recipes" ON recipes
    FOR INSERT WITH CHECK (auth.uid() = created_by);

CREATE POLICY "Users can update their own recipes" ON recipes
    FOR UPDATE USING (auth.uid() = created_by);

CREATE POLICY "Collaborators can update shared recipes" ON recipes
    FOR UPDATE USING (
        EXISTS (
            SELECT 1 FROM recipe_shares
            WHERE recipe_shares.recipe_id = recipes.id
            AND recipe_shares.shared_with_user_id = auth.uid()
            AND recipe_shares.permission_level = 'collaborate'
        )
    );

CREATE POLICY "Users can delete their own recipes" ON recipes
    FOR DELETE USING (auth.uid() = created_by);

-- User recipe data policies
CREATE POLICY "Users can manage their own recipe data" ON user_recipe_data
    FOR ALL USING (auth.uid() = user_id);

-- Cookbooks policies
CREATE POLICY "Public cookbooks are viewable by everyone" ON cookbooks
    FOR SELECT USING (is_public = true);

CREATE POLICY "Users can view their own cookbooks" ON cookbooks
    FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "Users can view shared cookbooks" ON cookbooks
    FOR SELECT USING (
        EXISTS (
            SELECT 1 FROM cookbook_shares
            WHERE cookbook_shares.cookbook_id = cookbooks.id
            AND cookbook_shares.shared_with_user_id = auth.uid()
        )
    );

CREATE POLICY "Users can manage their own cookbooks" ON cookbooks
    FOR ALL USING (auth.uid() = user_id);

-- Cookbook folders policies
CREATE POLICY "Users can manage folders in their cookbooks" ON cookbook_folders
    FOR ALL USING (
        EXISTS (
            SELECT 1 FROM cookbooks
            WHERE cookbooks.id = cookbook_folders.cookbook_id
            AND cookbooks.user_id = auth.uid()
        )
    );

-- Cookbook recipes policies
CREATE POLICY "Users can manage recipes in their cookbooks" ON cookbook_recipes
    FOR ALL USING (
        EXISTS (
            SELECT 1 FROM cookbooks
            WHERE cookbooks.id = cookbook_recipes.cookbook_id
            AND cookbooks.user_id = auth.uid()
        )
    );

-- Folder recipes policies
CREATE POLICY "Users can manage recipes in their folders" ON folder_recipes
    FOR ALL USING (
        EXISTS (
            SELECT 1 FROM cookbook_folders
            JOIN cookbooks ON cookbooks.id = cookbook_folders.cookbook_id
            WHERE cookbook_folders.id = folder_recipes.folder_id
            AND cookbooks.user_id = auth.uid()
        )
    );

-- Recipe shares policies
CREATE POLICY "Users can view shares for their recipes" ON recipe_shares
    FOR SELECT USING (auth.uid() = shared_by_user_id OR auth.uid() = shared_with_user_id);

CREATE POLICY "Users can share their recipes" ON recipe_shares
    FOR INSERT WITH CHECK (
        EXISTS (
            SELECT 1 FROM recipes
            WHERE recipes.id = recipe_shares.recipe_id
            AND recipes.created_by = auth.uid()
        )
    );

CREATE POLICY "Users can delete their shares" ON recipe_shares
    FOR DELETE USING (auth.uid() = shared_by_user_id);

-- Cookbook shares policies (similar to recipe shares)
CREATE POLICY "Users can view shares for their cookbooks" ON cookbook_shares
    FOR SELECT USING (auth.uid() = shared_by_user_id OR auth.uid() = shared_with_user_id);

CREATE POLICY "Users can share their cookbooks" ON cookbook_shares
    FOR INSERT WITH CHECK (
        EXISTS (
            SELECT 1 FROM cookbooks
            WHERE cookbooks.id = cookbook_shares.cookbook_id
            AND cookbooks.user_id = auth.uid()
        )
    );

CREATE POLICY "Users can delete their cookbook shares" ON cookbook_shares
    FOR DELETE USING (auth.uid() = shared_by_user_id);

-- Featured recipes policies (read-only for everyone, admin manages via service role)
CREATE POLICY "Everyone can view featured recipes" ON featured_recipes
    FOR SELECT USING (true);

-- Extraction jobs policies
CREATE POLICY "Users can manage their own extraction jobs" ON extraction_jobs
    FOR ALL USING (auth.uid() = user_id);

-- Recipe contributors policies
CREATE POLICY "Everyone can view recipe contributors" ON recipe_contributors
    FOR SELECT USING (true);

CREATE POLICY "System can manage recipe contributors" ON recipe_contributors
    FOR ALL USING (true);
