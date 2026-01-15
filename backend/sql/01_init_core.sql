-- 01_init_core.sql
-- Run this FIRST to set up the core database structure.

-- 1. Products Table
CREATE TABLE IF NOT EXISTS products (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    name TEXT NOT NULL,
    sku TEXT,
    category TEXT,
    description TEXT,
    keywords TEXT[], -- Array of strings
    status TEXT DEFAULT 'active', -- 'active', 'archived'
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL
);

-- 2. Reviews Table
CREATE TABLE IF NOT EXISTS reviews (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    product_id UUID REFERENCES products(id) ON DELETE CASCADE,
    platform TEXT NOT NULL, -- 'twitter', 'reddit', 'youtube', 'forums'
    text TEXT NOT NULL,
    author TEXT,
    source_url TEXT,
    text_hash TEXT UNIQUE, -- For deduplication
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL
);

-- 3. Sentiment Analysis Table
-- Stores the AI results linked 1:1 to a review
CREATE TABLE IF NOT EXISTS sentiment_analysis (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    review_id UUID REFERENCES reviews(id) ON DELETE CASCADE UNIQUE,
    product_id UUID REFERENCES products(id) ON DELETE CASCADE,
    label TEXT, -- 'POSITIVE', 'NEUTRAL', 'NEGATIVE'
    score NUMERIC, -- Confidence score 0.0 - 1.0
    emotions JSONB, -- Array of objects: [{"name": "joy", "score": 90}]
    credibility NUMERIC, -- 0-100 score
    credibility_reasons TEXT[], -- Array of strings explaining low credibility
    aspects JSONB, -- Array: [{"name": "Battery", "sentiment": "negative"}]
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL
);

-- 4. Enable RLS (Security)
ALTER TABLE products ENABLE ROW LEVEL SECURITY;
ALTER TABLE reviews ENABLE ROW LEVEL SECURITY;
ALTER TABLE sentiment_analysis ENABLE ROW LEVEL SECURITY;

-- 5. Open Access Policies (For Demo/Dev - Adjust for Prod as needed)
CREATE POLICY "Public read products" ON products FOR SELECT USING (true);
CREATE POLICY "Public insert products" ON products FOR INSERT WITH CHECK (true);

CREATE POLICY "Public read reviews" ON reviews FOR SELECT USING (true);
CREATE POLICY "Public insert reviews" ON reviews FOR INSERT WITH CHECK (true);

CREATE POLICY "Public read sentiment" ON sentiment_analysis FOR SELECT USING (true);
CREATE POLICY "Public insert sentiment" ON sentiment_analysis FOR INSERT WITH CHECK (true);
