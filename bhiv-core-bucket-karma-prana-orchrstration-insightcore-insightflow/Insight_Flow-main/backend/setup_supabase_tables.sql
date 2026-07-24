-- InsightFlow Database Schema for Supabase
-- Run these commands in your Supabase SQL Editor

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

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_routing_logs_created_at ON routing_logs(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_routing_logs_agent_id ON routing_logs(selected_agent_id);
CREATE INDEX IF NOT EXISTS idx_feedback_agent_id ON feedback_events(agent_id);
CREATE INDEX IF NOT EXISTS idx_agents_status ON agents(status);
CREATE INDEX IF NOT EXISTS idx_agents_type ON agents(type);

-- Insert sample agents
INSERT INTO agents (name, type, status, tags, capabilities, performance_score, success_rate) VALUES
('NLP Processor', 'nlp', 'active', ARRAY['text', 'classification'], 
 '[{"name": "text_classification", "description": "Classify text", "confidence_threshold": 0.8}]'::jsonb, 0.85, 0.90),
('TTS Generator', 'tts', 'active', ARRAY['audio', 'speech'], 
 '[{"name": "text_to_speech", "description": "Convert text to audio", "confidence_threshold": 0.7}]'::jsonb, 0.80, 0.85),
('Vision Analyzer', 'computer_vision', 'active', ARRAY['image', 'detection'], 
 '[{"name": "object_detection", "description": "Detect objects in images", "confidence_threshold": 0.75}]'::jsonb, 0.75, 0.80)
ON CONFLICT (id) DO NOTHING;

-- Enable Row Level Security (RLS) - Optional for security
ALTER TABLE agents ENABLE ROW LEVEL SECURITY;
ALTER TABLE routing_logs ENABLE ROW LEVEL SECURITY;
ALTER TABLE feedback_events ENABLE ROW LEVEL SECURITY;
ALTER TABLE q_learning_table ENABLE ROW LEVEL SECURITY;

-- Create policies for service role access
CREATE POLICY IF NOT EXISTS "Service role can access agents" ON agents FOR ALL USING (true);
CREATE POLICY IF NOT EXISTS "Service role can access routing_logs" ON routing_logs FOR ALL USING (true);
CREATE POLICY IF NOT EXISTS "Service role can access feedback_events" ON feedback_events FOR ALL USING (true);
CREATE POLICY IF NOT EXISTS "Service role can access q_learning_table" ON q_learning_table FOR ALL USING (true);