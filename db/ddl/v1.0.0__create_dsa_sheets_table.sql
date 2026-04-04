CREATE TABLE dsa_sheets (
    id TEXT PRIMARY KEY,                         -- "crackdsa_75"

    title TEXT NOT NULL,
    description TEXT,

    tags TEXT[] DEFAULT '{}',

    level TEXT CHECK (level IN ('beginner', 'intermediate', 'advanced')),

    estimated_hours INT,

    version INT DEFAULT 1,

    is_active BOOLEAN DEFAULT true,              -- soft delete
    is_public BOOLEAN DEFAULT true,              -- future: private sheets

    sheet_json JSONB NOT NULL,                   -- main structure

    created_by TEXT,                             -- admin/user id (future)

    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);


CREATE INDEX idx_dsa_sheets_active ON dsa_sheets(is_active);
CREATE INDEX idx_dsa_sheets_tags ON dsa_sheets USING GIN(tags);
CREATE INDEX idx_dsa_sheets_active_level ON dsa_sheets(is_active, level);