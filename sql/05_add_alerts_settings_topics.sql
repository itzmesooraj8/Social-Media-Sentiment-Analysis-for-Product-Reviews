-- Create alerts, user_settings, and topic_clusters tables
CREATE TABLE IF NOT EXISTS alerts (
    id SERIAL PRIMARY KEY,
    type VARCHAR(128) DEFAULT 'system',
    message TEXT NOT NULL,
    severity VARCHAR(32) NOT NULL DEFAULT 'medium',
    is_read BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS user_settings (
    user_id VARCHAR(255) NOT NULL,
    setting_key VARCHAR(255) NOT NULL,
    setting_value TEXT,
    PRIMARY KEY (user_id, setting_key)
);

CREATE TABLE IF NOT EXISTS topic_clusters (
    id SERIAL PRIMARY KEY,
    product_id VARCHAR(255),
    topic_name TEXT NOT NULL,
    sentiment_score DOUBLE PRECISION DEFAULT 0,
    mention_count INTEGER DEFAULT 0,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
