-- Ensure alerts table exists (safety migration)
CREATE TABLE IF NOT EXISTS alerts (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    type TEXT NOT NULL,
    severity TEXT CHECK (severity IN ('low', 'medium', 'high', 'critical')),
    message TEXT NOT NULL,
    is_read BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
