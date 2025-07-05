-- Create enum for request status
CREATE TYPE request_status AS ENUM ('pending', 'processing', 'completed', 'failed');

-- Create the diff_requests table
CREATE TABLE diff_requests (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    repo_url TEXT NOT NULL,
    prompt TEXT NOT NULL,
    enable_reflection BOOLEAN DEFAULT FALSE,
    status request_status DEFAULT 'pending',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Request metadata
    repo_owner TEXT,
    repo_name TEXT,
    user_id TEXT,
    
    -- Processing results
    initial_diff TEXT,
    final_diff TEXT,
    reflection_applied BOOLEAN DEFAULT FALSE,
    original_diff TEXT,
    
    -- GitHub integration results
    branch_name TEXT,
    pull_request_url TEXT,
    
    -- Error handling
    error_message TEXT,
    error_details TEXT,
    
    -- Performance metrics
    processing_time_seconds NUMERIC,
    openai_tokens_used INTEGER
);

-- Create indexes for better query performance
CREATE INDEX idx_diff_requests_status ON diff_requests(status);
CREATE INDEX idx_diff_requests_repo ON diff_requests(repo_owner, repo_name);
CREATE INDEX idx_diff_requests_created_at ON diff_requests(created_at DESC);
CREATE INDEX idx_diff_requests_user_id ON diff_requests(user_id);

-- Create updated_at trigger
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_diff_requests_updated_at
    BEFORE UPDATE ON diff_requests
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Create RLS (Row Level Security) policies if needed
ALTER TABLE diff_requests ENABLE ROW LEVEL SECURITY;

-- Policy to allow all operations for authenticated users (adjust as needed)
CREATE POLICY "Allow all operations for authenticated users" ON diff_requests
    FOR ALL USING (auth.role() = 'authenticated');

-- Policy to allow read access for anonymous users (optional)
CREATE POLICY "Allow read access for anonymous users" ON diff_requests
    FOR SELECT USING (true);

-- Create a view for public statistics (without sensitive data)
CREATE VIEW public_stats AS
SELECT 
    COUNT(*) as total_requests,
    COUNT(*) FILTER (WHERE status = 'completed') as completed_requests,
    COUNT(*) FILTER (WHERE status = 'failed') as failed_requests,
    COUNT(*) FILTER (WHERE status = 'pending') as pending_requests,
    COUNT(*) FILTER (WHERE status = 'processing') as processing_requests,
    COUNT(*) FILTER (WHERE reflection_applied = true) as reflection_requests,
    AVG(processing_time_seconds) FILTER (WHERE status = 'completed') as avg_processing_time,
    DATE_TRUNC('day', created_at) as date
FROM diff_requests
GROUP BY DATE_TRUNC('day', created_at)
ORDER BY date DESC;

-- Create a view for repository statistics
CREATE VIEW repo_stats AS
SELECT 
    repo_owner,
    repo_name,
    COUNT(*) as total_requests,
    COUNT(*) FILTER (WHERE status = 'completed') as completed_requests,
    COUNT(*) FILTER (WHERE status = 'failed') as failed_requests,
    MAX(created_at) as last_request_at
FROM diff_requests
WHERE repo_owner IS NOT NULL AND repo_name IS NOT NULL
GROUP BY repo_owner, repo_name
ORDER BY total_requests DESC;