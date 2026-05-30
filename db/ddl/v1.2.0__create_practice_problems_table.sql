-- DDL for practice_problems table
CREATE TABLE practice_problems (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),      -- Unique system-wide identifier
    
    slug TEXT UNIQUE NOT NULL,                          -- Beautiful URL slug (e.g. 'valid-palindrome')
    title TEXT NOT NULL,                                -- Problem title (e.g. 'Valid Palindrome')
    description TEXT,                                   -- Detailed description, examples, constraints (HTML from editor)
    
    difficulty TEXT NOT NULL CHECK (difficulty IN ('Easy', 'Medium', 'Hard')), -- Strict difficulty classification
    platform TEXT NOT NULL DEFAULT 'Internal',          -- Platform where the problem resides ('LeetCode', 'GFG', 'Internal', etc.)
    problem_url TEXT,                                   -- Direct link to platform practice environment (nullable)
    
    -- Consolidated JSONB bucket for rich programmatic solutions in multiple languages
    -- Structure: { "cpp": { "code": "...", "time_complexity": "O(N)", "space_complexity": "O(1)" } }
    solutions JSONB DEFAULT '{}'::jsonb,
    
    -- Consolidated JSONB bucket for related resources (videos, blogs, documentation)
    -- Structure: { "video_lectures": ["uuid-1", "uuid-2"], "blogs": [{"title": "...", "url": "..."}] }
    resources JSONB DEFAULT '{}'::jsonb,
    
    -- Consolidated JSONB bucket for categorization tags, metadata scores, and environment specifications
    -- Structure: { "tags": ["Two Pointers"], "company_tags": ["Google"], "importance_score": 9, "frequency_score": 8.5 }
    attributes JSONB DEFAULT '{}'::jsonb,
    
    is_active BOOLEAN DEFAULT true,                     -- Soft-delete state
    
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Optimization Indices for Rapid Filtering and Dynamic Querying
CREATE UNIQUE INDEX idx_practice_problems_slug ON practice_problems(slug);
CREATE INDEX idx_practice_problems_active ON practice_problems(is_active);
CREATE INDEX idx_practice_problems_active_difficulty ON practice_problems(is_active, difficulty);
CREATE INDEX idx_practice_problems_platform ON practice_problems(platform);

-- GIN Indices for extremely fast nested search/filtering inside JSONB columns
CREATE INDEX idx_practice_problems_solutions ON practice_problems USING GIN(solutions);
CREATE INDEX idx_practice_problems_resources ON practice_problems USING GIN(resources);
CREATE INDEX idx_practice_problems_attributes ON practice_problems USING GIN(attributes);
