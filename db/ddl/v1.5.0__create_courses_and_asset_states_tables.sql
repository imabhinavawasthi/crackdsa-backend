-- Create custom enum types for user asset interactions
CREATE TYPE asset_type_enum AS ENUM ('video', 'problem', 'article');
CREATE TYPE asset_status_enum AS ENUM ('pending', 'done', 'revision');

-- Create courses table
CREATE TABLE courses (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),      -- Standard system-wide UUID for internal references
    slug VARCHAR(255) UNIQUE NOT NULL,                 -- SEO-friendly text slug key (e.g. 'dsa-bootcamp-recordings')
    title TEXT NOT NULL,                                -- Course title
    description TEXT NOT NULL,                          -- Detailed description/pitch
    category TEXT NOT NULL,                             -- e.g. "core-dsa", "system-design", "advanced"
    
    -- List of instructor UUIDs pointing to instructors table
    instructor_ids UUID[] DEFAULT '{}',                 
    tags TEXT[] DEFAULT '{}',                           -- Marketing tags
    
    is_pro BOOLEAN DEFAULT true,                        -- Requires premium access
    is_popular BOOLEAN DEFAULT false,                   -- Marketing highlight badge
    
    price INT NOT NULL,                                 -- Current selling price
    original_price INT NOT NULL,                        -- Strikethrough price
    
    -- Structured syllabus JSONB: [{ "id": "sec-1", "title": "...", "items": [...], "subsections": [...] }]
    curriculum JSONB DEFAULT '[]'::jsonb,
    
    status TEXT NOT NULL DEFAULT 'draft',               -- 'active', 'upcoming', 'draft'
    is_active BOOLEAN DEFAULT true,                     -- Soft delete flag
    
    -- Extensible metadata bucket for dynamic overrides/UI parameters
    metadata JSONB DEFAULT '{}'::jsonb,
    
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Optimize queries by course state and categorization
CREATE UNIQUE INDEX idx_courses_slug ON courses(slug);
CREATE INDEX idx_courses_active ON courses(is_active, status);
CREATE INDEX idx_courses_category ON courses(category);
CREATE INDEX idx_courses_metadata ON courses USING GIN(metadata);

-- Create user_asset_states table to track individual progress, bookmarks, and notepad entries
CREATE TABLE user_asset_states (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL,                              -- References Supabase auth.users UUID
    
    asset_id TEXT NOT NULL,                             -- References video_lectures.id, practice_problems.slug, or articles.slug
    asset_type asset_type_enum NOT NULL,                -- 'video', 'problem', 'article'
    
    status asset_status_enum NOT NULL DEFAULT 'pending',-- 'pending', 'done', 'revision'
    is_bookmarked BOOLEAN DEFAULT false,                -- Bookmark status flag
    bookmarked_at TIMESTAMPTZ,                          -- Timestamp when bookmarked
    
    -- Notepad array: [{ "id": "note-1", "text": "...", "created_at": "..." }]
    notes JSONB DEFAULT '[]'::jsonb,
    
    -- Extensible metadata bucket for dynamic overrides/tracking metrics
    metadata JSONB DEFAULT '{}'::jsonb,
    
    last_interacted_at TIMESTAMPTZ DEFAULT NOW(),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    
    -- Ensure exactly one interaction status row exists per user/asset pair
    UNIQUE(user_id, asset_id, asset_type)
);

-- Indices for dynamic student dashboards and notepad retrievals
CREATE INDEX idx_user_asset_states_user ON user_asset_states(user_id);
CREATE INDEX idx_user_asset_states_lookup ON user_asset_states(user_id, asset_id, asset_type);
CREATE INDEX idx_user_asset_states_bookmarked ON user_asset_states(user_id) WHERE is_bookmarked = true;
CREATE INDEX idx_user_asset_states_notes ON user_asset_states USING GIN(notes);
CREATE INDEX idx_user_asset_states_metadata ON user_asset_states USING GIN(metadata);
