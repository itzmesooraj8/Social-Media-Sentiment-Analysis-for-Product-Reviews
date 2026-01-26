-- 1. ALIGN REVIEWS TABLE (Critical Fix)
-- Add 'text' column if it's missing (to match Frontend/Backend code)
ALTER TABLE public.reviews ADD COLUMN IF NOT EXISTS text TEXT;

-- If you have data in 'content', move it to 'text' so we don't lose it
UPDATE public.reviews SET text = content WHERE text IS NULL AND content IS NOT NULL;

-- Ensure other vital columns exist for the Analyzer
ALTER TABLE public.reviews ADD COLUMN IF NOT EXISTS sentiment_score FLOAT DEFAULT 0.0;
ALTER TABLE public.reviews ADD COLUMN IF NOT EXISTS sentiment_label TEXT DEFAULT 'neutral';
ALTER TABLE public.reviews ADD COLUMN IF NOT EXISTS credibility_score FLOAT DEFAULT 0.0;
ALTER TABLE public.reviews ADD COLUMN IF NOT EXISTS platform TEXT DEFAULT 'youtube';
ALTER TABLE public.reviews ADD COLUMN IF NOT EXISTS source_url TEXT;
ALTER TABLE public.reviews ADD COLUMN IF NOT EXISTS author TEXT DEFAULT 'Anonymous';

-- 2. ALIGN PRODUCTS TABLE
ALTER TABLE public.products ADD COLUMN IF NOT EXISTS status TEXT DEFAULT 'active';
ALTER TABLE public.products ADD COLUMN IF NOT EXISTS image_url TEXT;
ALTER TABLE public.products ADD COLUMN IF NOT EXISTS description TEXT;
ALTER TABLE public.products ADD COLUMN IF NOT EXISTS platform TEXT DEFAULT 'generic';
ALTER TABLE public.products ADD COLUMN IF NOT EXISTS last_updated TIMESTAMPTZ DEFAULT NOW();

-- 3. ENSURE PERMISSIONS (Security Requirement)
-- Allow the API (service_role and authenticated users) to Read/Write
GRANT ALL ON ALL TABLES IN SCHEMA public TO service_role;
GRANT ALL ON ALL TABLES IN SCHEMA public TO postgres;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO authenticated;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO anon;

-- 4. REFRESH CACHE
NOTIFY pgrst, 'reload schema';
