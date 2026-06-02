-- DDL migration to add profile and subscription columns to public.users table
ALTER TABLE public.users
ADD COLUMN IF NOT EXISTS college TEXT NULL,
ADD COLUMN IF NOT EXISTS graduation_year TEXT NULL,
ADD COLUMN IF NOT EXISTS branch TEXT NULL,
ADD COLUMN IF NOT EXISTS social_links JSONB NULL DEFAULT '{}'::jsonb,
ADD COLUMN IF NOT EXISTS metadata JSONB NULL DEFAULT '{}'::jsonb,
ADD COLUMN IF NOT EXISTS pro_subscription JSONB NULL DEFAULT '{}'::jsonb,
ADD COLUMN IF NOT EXISTS purchased_courses JSONB NULL DEFAULT '{}'::jsonb;
