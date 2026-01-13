-- Migration to add text_hash for caching
ALTER TABLE reviews ADD COLUMN IF NOT EXISTS text_hash TEXT;
CREATE INDEX IF NOT EXISTS idx_reviews_text_hash ON reviews(text_hash);

-- Backfill hashes for existing reviews (optional)
UPDATE reviews SET text_hash = md5(text) WHERE text_hash IS NULL;
