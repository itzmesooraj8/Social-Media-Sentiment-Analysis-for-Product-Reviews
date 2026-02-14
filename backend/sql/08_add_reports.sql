-- 08_add_reports.sql
-- Run this to enable persistent report history tracking.

CREATE TABLE IF NOT EXISTS reports (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    product_id UUID REFERENCES products(id) ON DELETE CASCADE,
    filename TEXT NOT NULL,
    storage_path TEXT NOT NULL, -- Path in Supabase Storage
    type TEXT NOT NULL, -- 'pdf', 'excel', 'csv'
    size BIGINT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL
);

-- Enable RLS
ALTER TABLE reports ENABLE ROW LEVEL SECURITY;

-- Public Policy (Open for demo/development)
CREATE POLICY "Public read reports" ON reports FOR SELECT USING (true);
CREATE POLICY "Public insert reports" ON reports FOR INSERT WITH CHECK (true);
CREATE POLICY "Public delete reports" ON reports FOR DELETE USING (true);
