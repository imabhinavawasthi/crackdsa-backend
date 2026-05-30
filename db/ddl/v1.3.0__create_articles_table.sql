CREATE TABLE articles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    slug TEXT UNIQUE NOT NULL,
    title TEXT NOT NULL,
    subtitle TEXT,
    description TEXT,
    cover_image TEXT,
    category TEXT NOT NULL DEFAULT 'General',
    difficulty TEXT,
    read_time_minutes INT DEFAULT 5,
    author_name TEXT,
    author_avatar TEXT,
    resources JSONB DEFAULT '{}'::jsonb,
    attributes JSONB DEFAULT '{}'::jsonb,
    is_published BOOLEAN DEFAULT false,
    is_active BOOLEAN DEFAULT true,
    published_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE UNIQUE INDEX idx_articles_slug ON articles(slug);
CREATE INDEX idx_articles_active ON articles(is_active);
CREATE INDEX idx_articles_published ON articles(is_published, is_active);
CREATE INDEX idx_articles_category ON articles(category);
CREATE INDEX idx_articles_resources ON articles USING GIN(resources);
CREATE INDEX idx_articles_attributes ON articles USING GIN(attributes);
