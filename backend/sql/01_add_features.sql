-- Migration to add text_hash to reviews and credibility_reasons to sentiment_analysis

-- 1. Add text_hash to reviews table for caching
ALTER TABLE reviews ADD COLUMN IF NOT EXISTS text_hash TEXT;
CREATE INDEX IF NOT EXISTS idx_reviews_text_hash ON reviews(text_hash);

-- Backfill hashes for existing reviews (optional - requires pgcrypto extension or app-side backfill)
-- UPDATE reviews SET text_hash = md5(text) WHERE text_hash IS NULL;

-- 2. Add credibility_reasons to sentiment_analysis table
ALTER TABLE sentiment_analysis ADD COLUMN IF NOT EXISTS credibility_reasons TEXT[];
