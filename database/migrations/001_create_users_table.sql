-- =============================================
-- USERS (PROFILES) TABLE
-- Extends auth.users with application-specific profile data
-- =============================================

CREATE TABLE public.users (
    -- Primary key matches auth.users.id (one-to-one relationship)
    id UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,

    -- Profile information
    name VARCHAR(100) NOT NULL,
    bio TEXT,
    date_of_birth DATE NOT NULL,

    -- Contact information (denormalized from auth.users for easier queries)
    email VARCHAR(255),
    phone VARCHAR(20),

    -- Profile completion tracking
    profile_completed BOOLEAN DEFAULT true, -- If record exists, profile is completed

    -- Avatar/profile picture
    avatar_url TEXT,

    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    -- Constraints
    CONSTRAINT name_not_empty CHECK (char_length(trim(name)) >= 1),
    CONSTRAINT bio_length CHECK (char_length(bio) <= 500)
);

-- Indexes
CREATE INDEX idx_users_email ON public.users(email);
CREATE INDEX idx_users_phone ON public.users(phone);
CREATE INDEX idx_users_created_at ON public.users(created_at DESC);

-- Full-text search on name
CREATE INDEX idx_users_search ON public.users USING GIN(
    to_tsvector('english', name)
);

-- Trigger for updated_at
CREATE TRIGGER update_users_updated_at
    BEFORE UPDATE ON public.users
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- =============================================
-- ROW LEVEL SECURITY (RLS) POLICIES
-- =============================================

ALTER TABLE public.users ENABLE ROW LEVEL SECURITY;

-- Users can view all profiles (for user discovery, sharing, etc.)
CREATE POLICY "Profiles are viewable by everyone"
    ON public.users
    FOR SELECT
    USING (true);

-- Users can insert their own profile (only once, during profile completion)
CREATE POLICY "Users can create their own profile"
    ON public.users
    FOR INSERT
    WITH CHECK (auth.uid() = id);

-- Users can update only their own profile
CREATE POLICY "Users can update their own profile"
    ON public.users
    FOR UPDATE
    USING (auth.uid() = id);

-- Users cannot delete their profile (must delete auth account)
-- Profile is automatically deleted when auth.users is deleted (CASCADE)

-- =============================================
-- COMMENTS FOR DOCUMENTATION
-- =============================================

COMMENT ON TABLE public.users IS 'User profiles extending auth.users with application-specific data';
COMMENT ON COLUMN public.users.id IS 'References auth.users.id (one-to-one)';
COMMENT ON COLUMN public.users.name IS 'Full name of the user';
COMMENT ON COLUMN public.users.profile_completed IS 'Always true if record exists; used to track completion';
COMMENT ON COLUMN public.users.email IS 'Denormalized from auth.users for easier queries';
COMMENT ON COLUMN public.users.phone IS 'Denormalized from auth.users for easier queries';
