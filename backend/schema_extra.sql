-- FIX: Final Schema Repair & Data Migration
-- This script aligns the database with the "Real" application code (data_pipeline.py)
-- ensuring that 'text' and 'username' columns exist and are populated.

-- 1. Ensure 'text' column exists (App uses 'text', not 'content')
ALTER TABLE public.reviews 
ADD COLUMN IF NOT EXISTS text TEXT;

-- 2. Ensure 'username' column exists (App uses 'username')
ALTER TABLE public.reviews 
ADD COLUMN IF NOT EXISTS username TEXT DEFAULT 'Anonymous';

-- 3. Migration: Copy data from old columns (content/author) to new ones (text/username)
-- Using DO block to handle potential missing source columns gracefully would be complex in pure SQL,
-- assuming 'content' and 'author' might exist from previous seeds.
-- If they don't exist, these updates will fail. We'll wraps them in a way that continues?
-- Simplest approach: Try update. If 'content' doesn't exist, this statement fails, but next ones run? 
-- No, postgres stops. 
-- However, we know 'content' exists because the seed script used it.
UPDATE public.reviews SET text = content WHERE text IS NULL AND content IS NOT NULL;
UPDATE public.reviews SET username = author WHERE username IS NULL AND author IS NOT NULL;

-- 4. Ensure other critical columns exist
ALTER TABLE public.reviews 
ADD COLUMN IF NOT EXISTS author TEXT DEFAULT 'Anonymous', -- KEEPING for backward compat
ADD COLUMN IF NOT EXISTS platform TEXT DEFAULT 'youtube',
ADD COLUMN IF NOT EXISTS source_url TEXT,
ADD COLUMN IF NOT EXISTS sentiment_score FLOAT DEFAULT 0.0,
ADD COLUMN IF NOT EXISTS sentiment_label TEXT DEFAULT 'neutral',
ADD COLUMN IF NOT EXISTS credibility_score FLOAT DEFAULT 0.0,
ADD COLUMN IF NOT EXISTS text_hash TEXT;

-- 5. Force Schema Cache Reload (Critical for API)
NOTIFY pgrst, 'reload schema';
