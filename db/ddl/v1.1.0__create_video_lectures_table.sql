-- Create video_lectures table as a pure reusable learning asset with consolidated JSONB structures
CREATE TABLE video_lectures (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),      -- Unique identifier for the lecture
    
    title TEXT NOT NULL,                                -- "Sliding Window Pattern Deep-dive"
    description TEXT,                                   -- Detailed lecture summary or notes
    
    video_url TEXT NOT NULL,                            -- Streamable URL (Cloudflare, YouTube, S3, Vimeo)
    duration_seconds INT DEFAULT 0,                     -- Video runtime (useful for course completion math)
    thumbnail_url TEXT,                                 -- Custom lecture splash screen
    
    -- Consolidated JSONB bucket for all SDE links (problems, articles/blogs, assignments, slides, code snippets)
    -- Structure: { "problems": [...], "blogs": [...], "assignments": [...], "slides": [...] }
    resources JSONB DEFAULT '{}'::jsonb,
    
    -- Consolidated JSONB bucket for player settings, timeline chapters, and video playback features
    -- Structure: { "chapters": [...], "allow_download": true, "subtitles": [...] }
    attributes JSONB DEFAULT '{}'::jsonb,
    
    is_active BOOLEAN DEFAULT true,                     -- Soft delete
    
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Indices for rapid active state lookup and dynamic JSONB search checks
CREATE INDEX idx_video_lectures_active ON video_lectures(is_active);
CREATE INDEX idx_video_lectures_resources ON video_lectures USING GIN(resources);
CREATE INDEX idx_video_lectures_attributes ON video_lectures USING GIN(attributes);
