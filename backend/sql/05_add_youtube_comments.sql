-- Add YouTube-specific columns and videos table to support dedup and incremental fetch
BEGIN;

-- Add comment_id and video_id to reviews table (if not exists)
ALTER TABLE IF EXISTS public.reviews
    ADD COLUMN IF NOT EXISTS comment_id TEXT;

ALTER TABLE IF EXISTS public.reviews
    ADD COLUMN IF NOT EXISTS video_id TEXT;

-- Create unique index on comment_id to prevent duplicates
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_indexes WHERE schemaname = 'public' AND indexname = 'idx_reviews_comment_id_unique'
    ) THEN
        CREATE UNIQUE INDEX idx_reviews_comment_id_unique ON public.reviews (comment_id) WHERE comment_id IS NOT NULL;
    END IF;
END$$;

-- Create videos table to track last checked time per video
CREATE TABLE IF NOT EXISTS public.videos (
    id serial PRIMARY KEY,
    video_id TEXT UNIQUE NOT NULL,
    title TEXT,
    product_id UUID,
    last_checked_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now()
);

COMMIT;
