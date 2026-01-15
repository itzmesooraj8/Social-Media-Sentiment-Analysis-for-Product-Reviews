-- 1. Create User Settings Table (if not exists)
-- Stores per-user configuration like alert thresholds.
CREATE TABLE IF NOT EXISTS user_settings (
    user_id UUID REFERENCES auth.users(id),
    setting_key TEXT NOT NULL,
    setting_value JSONB,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()),
    PRIMARY KEY (user_id, setting_key)
);

-- Enable RLS
ALTER TABLE user_settings ENABLE ROW LEVEL SECURITY;

-- Policy: Users can only see/edit their own settings
CREATE POLICY "Users can view own settings" ON user_settings
    FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "Users can update own settings" ON user_settings
    FOR UPDATE USING (auth.uid() = user_id);

CREATE POLICY "Users can insert own settings" ON user_settings
    FOR INSERT WITH CHECK (auth.uid() = user_id);


-- 2. Add Performance Indexes
-- optimize filtering by date for reports
CREATE INDEX IF NOT EXISTS idx_reviews_created_at ON reviews(created_at DESC);
-- optimize filtering reviews by platform
CREATE INDEX IF NOT EXISTS idx_reviews_platform ON reviews(platform);
-- optimize sentiment range queries (e.g. "show me negative reviews")
CREATE INDEX IF NOT EXISTS idx_sentiment_analysis_score ON sentiment_analysis(score);


-- 3. Create Daily Analytics View
-- Pre-calculates daily rollups for fast dashboard loading.
CREATE OR REPLACE VIEW analytics_summary AS
SELECT
    DATE(r.created_at) as report_date,
    COUNT(r.id) as total_daily_reviews,
    ROUND(AVG(COALESCE(s.score, 0.5))::numeric, 2) as avg_sentiment,
    ROUND(AVG(COALESCE(s.credibility, 0))::numeric, 2) as avg_credibility,
    jsonb_build_object(
        'twitter', COUNT(*) FILTER (WHERE r.platform = 'twitter'),
        'reddit', COUNT(*) FILTER (WHERE r.platform = 'reddit'),
        'youtube', COUNT(*) FILTER (WHERE r.platform = 'youtube'),
        'forums', COUNT(*) FILTER (WHERE r.platform = 'forums')
    ) as platform_breakdown
FROM
    reviews r
LEFT JOIN
    sentiment_analysis s ON r.id = s.review_id
GROUP BY
    DATE(r.created_at)
ORDER BY
    DATE(r.created_at) DESC;
