-- Insight Flow Database Setup for Supabase
-- Run this in Supabase SQL Editor: https://nzkqubedbeiqdxtpsves.supabase.co

-- Create agents table
CREATE TABLE IF NOT EXISTS agents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT NOT NULL,
    type TEXT NOT NULL,
    status TEXT DEFAULT 'active',
    capabilities JSONB DEFAULT '[]',
    performance_score FLOAT DEFAULT 0.5,
    success_rate FLOAT DEFAULT 0.5,
    average_latency FLOAT DEFAULT 0,
    total_requests INTEGER DEFAULT 0,
    successful_requests INTEGER DEFAULT 0,
    failed_requests INTEGER DEFAULT 0,
    tags TEXT[] DEFAULT '{}',
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Create routing_logs table
CREATE TABLE IF NOT EXISTS routing_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    request_id TEXT NOT NULL,
    user_id TEXT,
    input_type TEXT NOT NULL,
    input_data JSONB NOT NULL,
    selected_agent_id UUID REFERENCES agents(id),
    agent_name TEXT,
    confidence_score FLOAT,
    routing_reason TEXT,
    routing_strategy TEXT,
    status TEXT DEFAULT 'pending',
    execution_time_ms FLOAT,
    response_data JSONB,
    error_message TEXT,
    context JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Create feedback_events table
CREATE TABLE IF NOT EXISTS feedback_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    routing_log_id UUID REFERENCES routing_logs(id),
    agent_id UUID REFERENCES agents(id),
    feedback_type TEXT NOT NULL,
    success BOOLEAN NOT NULL,
    latency_ms FLOAT NOT NULL,
    accuracy_score FLOAT,
    user_satisfaction INTEGER CHECK (user_satisfaction BETWEEN 1 AND 5),
    error_details TEXT,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Create Q-learning table
CREATE TABLE IF NOT EXISTS q_learning_table (
    state TEXT NOT NULL,
    action TEXT NOT NULL,
    q_value FLOAT DEFAULT 0,
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    PRIMARY KEY (state, action)
);

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_routing_logs_created_at ON routing_logs(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_routing_logs_agent_id ON routing_logs(selected_agent_id);
CREATE INDEX IF NOT EXISTS idx_feedback_agent_id ON feedback_events(agent_id);
CREATE INDEX IF NOT EXISTS idx_agents_status ON agents(status);

-- Insert sample agents for BHIV Core integration
INSERT INTO agents (name, type, status, tags, capabilities) VALUES
('edumentor_agent', 'nlp', 'active', ARRAY['text', 'education', 'qa'], 
 '[{"name": "question_answering", "description": "Educational Q&A", "confidence_threshold": 0.8}]'::jsonb),
('stream_transformer_agent', 'nlp', 'active', ARRAY['text', 'general'], 
 '[{"name": "text_processing", "description": "General text processing", "confidence_threshold": 0.7}]'::jsonb),
('knowledge_agent', 'nlp', 'active', ARRAY['text', 'knowledge', 'search'], 
 '[{"name": "knowledge_search", "description": "Knowledge base search", "confidence_threshold": 0.75}]'::jsonb),
('image_agent', 'computer_vision', 'active', ARRAY['image', 'analysis'], 
 '[{"name": "image_analysis", "description": "Image processing", "confidence_threshold": 0.75}]'::jsonb),
('audio_agent', 'audio', 'active', ARRAY['audio', 'transcription'], 
 '[{"name": "audio_processing", "description": "Audio transcription", "confidence_threshold": 0.7}]'::jsonb),
('archive_agent', 'document', 'active', ARRAY['pdf', 'document'], 
 '[{"name": "document_processing", "description": "PDF processing", "confidence_threshold": 0.75}]'::jsonb)
ON CONFLICT DO NOTHING;

-- Verify setup
SELECT 'Setup complete! Agents created:' as status;
SELECT name, type, status FROM agents;
