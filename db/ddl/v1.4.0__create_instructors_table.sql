-- Create instructors table for course instructor profiles
-- Instructors are reusable across multiple courses
CREATE TABLE instructors (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    name TEXT NOT NULL,                        -- "Abhinav Awasthi", "John Doe"
    role TEXT NOT NULL,                        -- "Founder", "Senior Mentor", "Course Creator", etc.
    sub_title TEXT,                            -- "Ex-Google SDE", "Ex-Amazon Principal Engineer"
    
    bio TEXT,                                  -- Extended description/biography
    profile_image_url TEXT,                    -- Avatar/profile picture URL
    
    -- Flexible metadata for UI customization, social links, etc.
    -- Example: { "color": "from-brand-500 to-blue-light-400", "twitter": "@username", "linkedin": "..." }
    metadata JSONB DEFAULT '{}'::jsonb,
    
    is_active BOOLEAN DEFAULT true,            -- Soft delete
    
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Index for rapid lookups by active status
CREATE INDEX idx_instructors_active ON instructors(is_active);

-- Index for name-based search (future use)
CREATE INDEX idx_instructors_name ON instructors(name);
