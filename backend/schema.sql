-- Sentiment Beacon Database Schema
-- Run this in your Supabase SQL Editor

-- Products Table
CREATE TABLE IF NOT EXISTS products (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    name TEXT NOT NULL,
    sku TEXT UNIQUE NOT NULL,
    category TEXT NOT NULL,
    description TEXT,
    keywords TEXT[],
    status TEXT DEFAULT 'active' CHECK (status IN ('active', 'paused', 'archived')),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Reviews Table
CREATE TABLE IF NOT EXISTS reviews (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    product_id UUID REFERENCES products(id) ON DELETE CASCADE,
    text TEXT NOT NULL,
    platform TEXT NOT NULL,
    source_url TEXT,
    author TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Sentiment Analysis Table
CREATE TABLE IF NOT EXISTS sentiment_analysis (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    review_id UUID REFERENCES reviews(id) ON DELETE CASCADE,
    product_id UUID REFERENCES products(id) ON DELETE CASCADE,
    label TEXT NOT NULL CHECK (label IN ('POSITIVE', 'NEGATIVE', 'NEUTRAL', 'ERROR')),
    score DECIMAL(5, 4),
    emotions JSONB DEFAULT '[]'::jsonb,
    credibility DECIMAL(5, 2),
    aspects JSONB DEFAULT '[]'::jsonb,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Integrations Table (for API keys)
CREATE TABLE IF NOT EXISTS integrations (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    platform TEXT UNIQUE NOT NULL,
    api_key TEXT NOT NULL,
    active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Alerts Table
CREATE TABLE IF NOT EXISTS alerts (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    type TEXT NOT NULL CHECK (type IN ('bot_detected', 'spam_cluster', 'review_surge', 'sentiment_shift', 'fake_review')),
    severity TEXT NOT NULL CHECK (severity IN ('low', 'medium', 'high', 'critical')),
    message TEXT NOT NULL,
    metadata JSONB DEFAULT '{}'::jsonb,
    resolved BOOLEAN DEFAULT false,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create indexes for better query performance
CREATE INDEX IF NOT EXISTS idx_reviews_product_id ON reviews(product_id);
CREATE INDEX IF NOT EXISTS idx_reviews_created_at ON reviews(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_sentiment_product_id ON sentiment_analysis(product_id);
CREATE INDEX IF NOT EXISTS idx_sentiment_label ON sentiment_analysis(label);
CREATE INDEX IF NOT EXISTS idx_alerts_created_at ON alerts(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_alerts_severity ON alerts(severity);

-- Enable Row Level Security (RLS)
ALTER TABLE products ENABLE ROW LEVEL SECURITY;
ALTER TABLE reviews ENABLE ROW LEVEL SECURITY;
ALTER TABLE sentiment_analysis ENABLE ROW LEVEL SECURITY;
ALTER TABLE integrations ENABLE ROW LEVEL SECURITY;
ALTER TABLE alerts ENABLE ROW LEVEL SECURITY;

-- Create policies for public access (adjust based on your security needs)
-- For development, we'll allow all operations. In production, add proper authentication.

-- Products policies
CREATE POLICY "Allow public read access on products" ON products FOR SELECT USING (true);
CREATE POLICY "Allow public insert on products" ON products FOR INSERT WITH CHECK (true);
CREATE POLICY "Allow public update on products" ON products FOR UPDATE USING (true);
CREATE POLICY "Allow public delete on products" ON products FOR DELETE USING (true);

-- Reviews policies
CREATE POLICY "Allow public read access on reviews" ON reviews FOR SELECT USING (true);
CREATE POLICY "Allow public insert on reviews" ON reviews FOR INSERT WITH CHECK (true);
CREATE POLICY "Allow public update on reviews" ON reviews FOR UPDATE USING (true);
CREATE POLICY "Allow public delete on reviews" ON reviews FOR DELETE USING (true);

-- Sentiment analysis policies
CREATE POLICY "Allow public read access on sentiment_analysis" ON sentiment_analysis FOR SELECT USING (true);
CREATE POLICY "Allow public insert on sentiment_analysis" ON sentiment_analysis FOR INSERT WITH CHECK (true);
CREATE POLICY "Allow public update on sentiment_analysis" ON sentiment_analysis FOR UPDATE USING (true);
CREATE POLICY "Allow public delete on sentiment_analysis" ON sentiment_analysis FOR DELETE USING (true);

-- Integrations policies
CREATE POLICY "Allow public read access on integrations" ON integrations FOR SELECT USING (true);
CREATE POLICY "Allow public insert on integrations" ON integrations FOR INSERT WITH CHECK (true);
CREATE POLICY "Allow public update on integrations" ON integrations FOR UPDATE USING (true);
CREATE POLICY "Allow public delete on integrations" ON integrations FOR DELETE USING (true);

-- Alerts policies
CREATE POLICY "Allow public read access on alerts" ON alerts FOR SELECT USING (true);
CREATE POLICY "Allow public insert on alerts" ON alerts FOR INSERT WITH CHECK (true);
CREATE POLICY "Allow public update on alerts" ON alerts FOR UPDATE USING (true);
CREATE POLICY "Allow public delete on alerts" ON alerts FOR DELETE USING (true);

-- Insert sample data
INSERT INTO products (name, sku, category, description, keywords) VALUES
('Ultra Pro Wireless Headphones', 'UPHW-001', 'Electronics', 'Premium wireless headphones with noise cancellation', ARRAY['headphones', 'wireless', 'audio']),
('Smart Home Hub 2.0', 'SHH-200', 'Smart Home', 'Central hub for all your smart home devices', ARRAY['smart home', 'hub', 'automation']),
('Premium Fitness Tracker', 'PFT-350', 'Wearables', 'Advanced fitness tracking with heart rate monitoring', ARRAY['fitness', 'tracker', 'health'])
ON CONFLICT (sku) DO NOTHING;

-- Insert sample reviews
INSERT INTO reviews (product_id, text, platform, author) 
SELECT 
    p.id,
    'Great product! Really love the quality and features.',
    'twitter',
    'user123'
FROM products p WHERE p.sku = 'UPHW-001'
LIMIT 1
ON CONFLICT DO NOTHING;

INSERT INTO reviews (product_id, text, platform, author) 
SELECT 
    p.id,
    'Not worth the price. Battery life is disappointing.',
    'reddit',
    'user456'
FROM products p WHERE p.sku = 'PFT-350'
LIMIT 1
ON CONFLICT DO NOTHING;
