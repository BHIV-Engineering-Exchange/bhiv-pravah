-- BHIV HR Platform - Production Schema Deployment v4.3.0
-- Fix missing columns and tables for production deployment + RL Tables

-- Add missing columns to clients table
ALTER TABLE clients 
ADD COLUMN IF NOT EXISTS failed_login_attempts INTEGER DEFAULT 0,
ADD COLUMN IF NOT EXISTS locked_until TIMESTAMP;

-- Update existing records
UPDATE clients 
SET failed_login_attempts = 0 
WHERE failed_login_attempts IS NULL;

-- Create job_applications table if not exists
CREATE TABLE IF NOT EXISTS job_applications (
    id SERIAL PRIMARY KEY,
    candidate_id INTEGER NOT NULL REFERENCES candidates(id) ON DELETE CASCADE,
    job_id INTEGER NOT NULL REFERENCES jobs(id) ON DELETE CASCADE,
    cover_letter TEXT,
    status VARCHAR(50) DEFAULT 'applied' CHECK (status IN ('applied', 'reviewed', 'shortlisted', 'rejected', 'withdrawn')),
    applied_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(candidate_id, job_id)
);

-- Add indexes for job_applications
CREATE INDEX IF NOT EXISTS idx_job_applications_candidate ON job_applications(candidate_id);
CREATE INDEX IF NOT EXISTS idx_job_applications_job ON job_applications(job_id);
CREATE INDEX IF NOT EXISTS idx_job_applications_status ON job_applications(status);
CREATE INDEX IF NOT EXISTS idx_job_applications_date ON job_applications(applied_date);

-- Add update trigger for job_applications
CREATE TRIGGER update_job_applications_updated_at 
BEFORE UPDATE ON job_applications 
FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- ============================================================================
-- RL + FEEDBACK AGENT TABLES (Ishan's Integration)
-- ============================================================================

-- RL Predictions & Scoring
CREATE TABLE IF NOT EXISTS rl_predictions (
    id SERIAL PRIMARY KEY,
    candidate_id INTEGER NOT NULL REFERENCES candidates(id) ON DELETE CASCADE,
    job_id INTEGER NOT NULL REFERENCES jobs(id) ON DELETE CASCADE,
    rl_score DECIMAL(5,2) NOT NULL CHECK (rl_score >= 0 AND rl_score <= 100),
    confidence_level DECIMAL(5,2) NOT NULL CHECK (confidence_level >= 0 AND confidence_level <= 100),
    decision_type VARCHAR(50) NOT NULL CHECK (decision_type IN ('recommend', 'review', 'reject')),
    features JSONB NOT NULL,
    model_version VARCHAR(20) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Feedback & Reward Signals
CREATE TABLE IF NOT EXISTS rl_feedback (
    id SERIAL PRIMARY KEY,
    prediction_id INTEGER REFERENCES rl_predictions(id) ON DELETE CASCADE,
    feedback_source VARCHAR(50) NOT NULL CHECK (feedback_source IN ('hr', 'client', 'candidate', 'system', 'workflow_automation')),
    actual_outcome VARCHAR(50) NOT NULL CHECK (actual_outcome IN ('hired', 'rejected', 'withdrawn', 'interviewed', 'shortlisted', 'pending')),
    feedback_score DECIMAL(5,2) NOT NULL CHECK (feedback_score >= 1 AND feedback_score <= 5),
    reward_signal DECIMAL(5,2) NOT NULL,
    feedback_notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- RL Model Performance Tracking
CREATE TABLE IF NOT EXISTS rl_model_performance (
    id SERIAL PRIMARY KEY,
    model_version VARCHAR(20) NOT NULL,
    accuracy DECIMAL(5,4) NOT NULL CHECK (accuracy >= 0 AND accuracy <= 1),
    precision_score DECIMAL(5,4) NOT NULL CHECK (precision_score >= 0 AND precision_score <= 1),
    recall_score DECIMAL(5,4) NOT NULL CHECK (recall_score >= 0 AND recall_score <= 1),
    f1_score DECIMAL(5,4) NOT NULL CHECK (f1_score >= 0 AND f1_score <= 1),
    average_reward DECIMAL(5,2) NOT NULL,
    total_predictions INTEGER NOT NULL CHECK (total_predictions >= 0),
    evaluation_date TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- RL Training Data
CREATE TABLE IF NOT EXISTS rl_training_data (
    id SERIAL PRIMARY KEY,
    candidate_features JSONB NOT NULL,
    job_features JSONB NOT NULL,
    match_score DECIMAL(5,2) NOT NULL CHECK (match_score >= 0 AND match_score <= 100),
    actual_outcome VARCHAR(50) NOT NULL,
    reward_value DECIMAL(5,2) NOT NULL,
    training_batch VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- RL Tables indexes
CREATE INDEX IF NOT EXISTS idx_rl_predictions_candidate_job ON rl_predictions(candidate_id, job_id);
CREATE INDEX IF NOT EXISTS idx_rl_predictions_created ON rl_predictions(created_at);
CREATE INDEX IF NOT EXISTS idx_rl_feedback_prediction ON rl_feedback(prediction_id);
CREATE INDEX IF NOT EXISTS idx_rl_feedback_outcome ON rl_feedback(actual_outcome, created_at);
CREATE INDEX IF NOT EXISTS idx_rl_performance_version ON rl_model_performance(model_version);
CREATE INDEX IF NOT EXISTS idx_rl_training_batch ON rl_training_data(training_batch);

-- Initialize RL model performance record
INSERT INTO rl_model_performance (
    model_version, accuracy, precision_score, recall_score, f1_score, 
    average_reward, total_predictions, evaluation_date
) VALUES (
    'v1.0.0', 0.0, 0.0, 0.0, 0.0, 0.0, 0, CURRENT_TIMESTAMP
) ON CONFLICT DO NOTHING;

-- Update schema version
INSERT INTO schema_version (version, description) VALUES 
('4.3.0', 'Production schema with RL + Feedback Agent tables (Ishan integration)'),
('4.2.0', 'Production schema with job_applications table and client auth fixes')
ON CONFLICT (version) DO UPDATE SET applied_at = CURRENT_TIMESTAMP;

-- Verify deployment
SELECT 'Schema v4.3.0 deployed successfully with RL + Feedback Agent integration' as status,
       COUNT(*) as total_tables
FROM information_schema.tables 
WHERE table_schema = 'public';

-- Show critical tables status
SELECT table_name, 
       CASE WHEN table_name IN ('clients', 'job_applications', 'rl_predictions', 'rl_feedback') THEN 'CRITICAL' ELSE 'OK' END as priority
FROM information_schema.tables 
WHERE table_schema = 'public' 
AND table_name IN ('clients', 'candidates', 'jobs', 'job_applications', 'feedback', 'rl_predictions', 'rl_feedback', 'rl_model_performance', 'rl_training_data')
ORDER BY table_name;