-- BHIV HR Platform - Consolidated Database Schema
-- Complete unified schema with Phase 3 learning engine
-- Version: 4.2.1 - Production Ready with All Missing Components
-- Generated: November 11, 2025
-- Includes: All extensions, triggers, functions, and missing columns

-- Enable required PostgreSQL extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_stat_statements";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

-- ============================================================================
-- CORE TABLES (Based on Gateway API Requirements)
-- ============================================================================

-- 1. CANDIDATES TABLE (Primary entity for all candidate operations)
CREATE TABLE IF NOT EXISTS candidates (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    phone VARCHAR(50),
    location VARCHAR(255),
    experience_years INTEGER DEFAULT 0 CHECK (experience_years >= 0),
    technical_skills TEXT,
    seniority_level VARCHAR(100),
    education_level VARCHAR(255),
    resume_path VARCHAR(500),
    password_hash VARCHAR(255),
    average_score DECIMAL(3,2) DEFAULT 0.0 CHECK (average_score >= 0 AND average_score <= 5),
    status VARCHAR(50) DEFAULT 'applied' CHECK (status IN ('applied', 'screened', 'interviewed', 'offered', 'hired', 'rejected')),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 2. JOBS TABLE (Job postings from clients and HR)
CREATE TABLE IF NOT EXISTS jobs (
    id SERIAL PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    department VARCHAR(255) NOT NULL,
    location VARCHAR(255) NOT NULL,
    experience_level VARCHAR(100) NOT NULL,
    requirements TEXT NOT NULL,
    description TEXT NOT NULL,
    employment_type VARCHAR(50) DEFAULT 'Full-time' CHECK (employment_type IN ('Full-time', 'Part-time', 'Contract', 'Intern')),
    client_id VARCHAR(100),
    status VARCHAR(50) DEFAULT 'active' CHECK (status IN ('active', 'paused', 'closed', 'draft')),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 3. FEEDBACK TABLE (Values assessment - core BHIV feature)
CREATE TABLE IF NOT EXISTS feedback (
    id SERIAL PRIMARY KEY,
    candidate_id INTEGER NOT NULL REFERENCES candidates(id) ON DELETE CASCADE,
    job_id INTEGER NOT NULL REFERENCES jobs(id) ON DELETE CASCADE,
    integrity INTEGER NOT NULL CHECK (integrity >= 1 AND integrity <= 5),
    honesty INTEGER NOT NULL CHECK (honesty >= 1 AND honesty <= 5),
    discipline INTEGER NOT NULL CHECK (discipline >= 1 AND discipline <= 5),
    hard_work INTEGER NOT NULL CHECK (hard_work >= 1 AND hard_work <= 5),
    gratitude INTEGER NOT NULL CHECK (gratitude >= 1 AND gratitude <= 5),
    average_score DECIMAL(3,2) GENERATED ALWAYS AS ((integrity + honesty + discipline + hard_work + gratitude) / 5.0) STORED,
    comments TEXT,
    reviewer_name VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 4. INTERVIEWS TABLE (Interview scheduling and management)
CREATE TABLE IF NOT EXISTS interviews (
    id SERIAL PRIMARY KEY,
    candidate_id INTEGER NOT NULL REFERENCES candidates(id) ON DELETE CASCADE,
    job_id INTEGER NOT NULL REFERENCES jobs(id) ON DELETE CASCADE,
    interview_date TIMESTAMP NOT NULL,
    interviewer VARCHAR(255) DEFAULT 'HR Team',
    interview_type VARCHAR(100) DEFAULT 'Technical' CHECK (interview_type IN ('Technical', 'HR', 'Behavioral', 'Final', 'Panel')),
    notes TEXT,
    status VARCHAR(50) DEFAULT 'scheduled' CHECK (status IN ('scheduled', 'completed', 'cancelled', 'rescheduled')),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 5. OFFERS TABLE (Job offer management)
CREATE TABLE IF NOT EXISTS offers (
    id SERIAL PRIMARY KEY,
    candidate_id INTEGER NOT NULL REFERENCES candidates(id) ON DELETE CASCADE,
    job_id INTEGER NOT NULL REFERENCES jobs(id) ON DELETE CASCADE,
    salary DECIMAL(12,2) NOT NULL CHECK (salary > 0),
    start_date DATE NOT NULL,
    terms TEXT NOT NULL,
    status VARCHAR(50) DEFAULT 'pending' CHECK (status IN ('pending', 'accepted', 'rejected', 'withdrawn', 'expired')),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- AUTHENTICATION & SECURITY TABLES
-- ============================================================================

-- 6. USERS TABLE (Internal HR users with 2FA support)
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(100) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    totp_secret VARCHAR(32),
    is_2fa_enabled BOOLEAN DEFAULT FALSE,
    role VARCHAR(50) DEFAULT 'user' CHECK (role IN ('admin', 'hr_manager', 'recruiter', 'user')),
    status VARCHAR(50) DEFAULT 'active' CHECK (status IN ('active', 'inactive', 'suspended')),
    last_login TIMESTAMP,
    failed_login_attempts INTEGER DEFAULT 0,
    locked_until TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 7. CLIENTS TABLE (External client companies with enhanced security)
CREATE TABLE IF NOT EXISTS clients (
    id SERIAL PRIMARY KEY,
    client_id VARCHAR(100) UNIQUE NOT NULL,
    client_name VARCHAR(255),
    company_name VARCHAR(255) NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    email VARCHAR(255) UNIQUE,
    phone VARCHAR(20),
    totp_secret VARCHAR(255),
    two_factor_enabled BOOLEAN DEFAULT FALSE,
    backup_codes TEXT,
    status VARCHAR(50) DEFAULT 'active' CHECK (status IN ('active', 'inactive', 'suspended')),
    password_changed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    password_history TEXT,
    failed_login_attempts INTEGER DEFAULT 0,
    locked_until TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Add missing columns to existing clients table (for production sync)
ALTER TABLE clients ADD COLUMN IF NOT EXISTS totp_secret VARCHAR(255);
ALTER TABLE clients ADD COLUMN IF NOT EXISTS two_factor_enabled BOOLEAN DEFAULT FALSE;
ALTER TABLE clients ADD COLUMN IF NOT EXISTS backup_codes TEXT;
ALTER TABLE clients ADD COLUMN IF NOT EXISTS password_changed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP;
ALTER TABLE clients ADD COLUMN IF NOT EXISTS password_history TEXT;

-- ============================================================================
-- AI & PERFORMANCE TABLES
-- ============================================================================

-- 8. MATCHING_CACHE TABLE (AI matching results cache)
CREATE TABLE IF NOT EXISTS matching_cache (
    id SERIAL PRIMARY KEY,
    job_id INTEGER NOT NULL REFERENCES jobs(id) ON DELETE CASCADE,
    candidate_id INTEGER NOT NULL REFERENCES candidates(id) ON DELETE CASCADE,
    match_score DECIMAL(5,2) NOT NULL CHECK (match_score >= 0 AND match_score <= 100),
    skills_match_score DECIMAL(5,2) DEFAULT 0,
    experience_match_score DECIMAL(5,2) DEFAULT 0,
    location_match_score DECIMAL(5,2) DEFAULT 0,
    values_alignment_score DECIMAL(3,2) DEFAULT 0,
    algorithm_version VARCHAR(50) DEFAULT 'v2.0.0',
    reasoning TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(job_id, candidate_id, algorithm_version)
);

-- ============================================================================
-- SECURITY & AUDIT TABLES
-- ============================================================================

-- 9. AUDIT_LOGS TABLE (Security and compliance tracking)
CREATE TABLE IF NOT EXISTS audit_logs (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    client_id VARCHAR(100) REFERENCES clients(client_id),
    action VARCHAR(100) NOT NULL,
    resource VARCHAR(100),
    resource_id INTEGER,
    ip_address INET,
    user_agent TEXT,
    request_method VARCHAR(10),
    endpoint VARCHAR(255),
    success BOOLEAN DEFAULT TRUE,
    error_message TEXT,
    details JSONB,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 10. RATE_LIMITS TABLE (API rate limiting)
CREATE TABLE IF NOT EXISTS rate_limits (
    id SERIAL PRIMARY KEY,
    ip_address INET NOT NULL,
    endpoint VARCHAR(255) NOT NULL,
    user_tier VARCHAR(50) DEFAULT 'default' CHECK (user_tier IN ('default', 'premium', 'enterprise')),
    request_count INTEGER DEFAULT 1,
    window_start TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    blocked_until TIMESTAMP,
    UNIQUE(ip_address, endpoint)
);

-- 11. CSP_VIOLATIONS TABLE (Content Security Policy violations)
CREATE TABLE IF NOT EXISTS csp_violations (
    id SERIAL PRIMARY KEY,
    violated_directive VARCHAR(255) NOT NULL,
    blocked_uri TEXT NOT NULL,
    document_uri TEXT NOT NULL,
    ip_address INET,
    user_agent TEXT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- PHASE 3: AI LEARNING ENGINE TABLES
-- ============================================================================

-- 12. COMPANY_SCORING_PREFERENCES TABLE (Phase 3 learning engine)
CREATE TABLE IF NOT EXISTS company_scoring_preferences (
    id SERIAL PRIMARY KEY,
    client_id VARCHAR(100) REFERENCES clients(client_id),
    scoring_weights JSONB,
    avg_satisfaction DECIMAL(3,2),
    feedback_count INTEGER,
    preferred_experience DECIMAL(5,2),
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

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

-- 13. JOB_APPLICATIONS TABLE (Candidate job applications)
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

-- 14. WORKFLOWS TABLE (LangGraph workflow tracking)
CREATE TABLE IF NOT EXISTS workflows (
    id SERIAL PRIMARY KEY,
    workflow_id VARCHAR(100) UNIQUE NOT NULL,
    workflow_type VARCHAR(100) NOT NULL CHECK (workflow_type IN ('candidate_application', 'candidate_shortlisted', 'interview_scheduled', 'custom')),
    status VARCHAR(50) DEFAULT 'running' CHECK (status IN ('running', 'completed', 'failed', 'cancelled')),
    candidate_id INTEGER REFERENCES candidates(id) ON DELETE SET NULL,
    job_id INTEGER REFERENCES jobs(id) ON DELETE SET NULL,
    client_id VARCHAR(100) REFERENCES clients(client_id) ON DELETE SET NULL,
    progress_percentage INTEGER DEFAULT 0 CHECK (progress_percentage >= 0 AND progress_percentage <= 100),
    current_step VARCHAR(255),
    total_steps INTEGER DEFAULT 1,
    input_data JSONB,
    output_data JSONB,
    error_message TEXT,
    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- PERFORMANCE INDEXES
-- ============================================================================

-- Candidates table indexes
CREATE INDEX IF NOT EXISTS idx_candidates_email ON candidates(email);
CREATE INDEX IF NOT EXISTS idx_candidates_status ON candidates(status);
CREATE INDEX IF NOT EXISTS idx_candidates_location ON candidates(location);
CREATE INDEX IF NOT EXISTS idx_candidates_experience ON candidates(experience_years);
CREATE INDEX IF NOT EXISTS idx_candidates_score ON candidates(average_score);
CREATE INDEX IF NOT EXISTS idx_candidates_skills_gin ON candidates USING gin(to_tsvector('english', technical_skills));
CREATE INDEX IF NOT EXISTS idx_candidates_created_at ON candidates(created_at);

-- Jobs table indexes
CREATE INDEX IF NOT EXISTS idx_jobs_status ON jobs(status);
CREATE INDEX IF NOT EXISTS idx_jobs_client_id ON jobs(client_id);
CREATE INDEX IF NOT EXISTS idx_jobs_department ON jobs(department);
CREATE INDEX IF NOT EXISTS idx_jobs_location ON jobs(location);
CREATE INDEX IF NOT EXISTS idx_jobs_experience_level ON jobs(experience_level);
CREATE INDEX IF NOT EXISTS idx_jobs_created_at ON jobs(created_at);

-- Feedback table indexes
CREATE INDEX IF NOT EXISTS idx_feedback_candidate_id ON feedback(candidate_id);
CREATE INDEX IF NOT EXISTS idx_feedback_job_id ON feedback(job_id);
CREATE INDEX IF NOT EXISTS idx_feedback_average_score ON feedback(average_score);
CREATE INDEX IF NOT EXISTS idx_feedback_created_at ON feedback(created_at);

-- Interviews table indexes
CREATE INDEX IF NOT EXISTS idx_interviews_candidate_id ON interviews(candidate_id);
CREATE INDEX IF NOT EXISTS idx_interviews_job_id ON interviews(job_id);
CREATE INDEX IF NOT EXISTS idx_interviews_date ON interviews(interview_date);
CREATE INDEX IF NOT EXISTS idx_interviews_status ON interviews(status);
CREATE INDEX IF NOT EXISTS idx_interviews_type ON interviews(interview_type);

-- Offers table indexes
CREATE INDEX IF NOT EXISTS idx_offers_candidate_id ON offers(candidate_id);
CREATE INDEX IF NOT EXISTS idx_offers_job_id ON offers(job_id);
CREATE INDEX IF NOT EXISTS idx_offers_status ON offers(status);
CREATE INDEX IF NOT EXISTS idx_offers_created_at ON offers(created_at);

-- Users table indexes
CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_users_status ON users(status);
CREATE INDEX IF NOT EXISTS idx_users_2fa_enabled ON users(is_2fa_enabled);
CREATE INDEX IF NOT EXISTS idx_users_last_login ON users(last_login);

-- Clients table indexes
CREATE INDEX IF NOT EXISTS idx_clients_client_id ON clients(client_id);
CREATE INDEX IF NOT EXISTS idx_clients_email ON clients(email);
CREATE INDEX IF NOT EXISTS idx_clients_status ON clients(status);
CREATE INDEX IF NOT EXISTS idx_clients_2fa_enabled ON clients(two_factor_enabled);

-- Matching cache indexes
CREATE INDEX IF NOT EXISTS idx_matching_job_id ON matching_cache(job_id);
CREATE INDEX IF NOT EXISTS idx_matching_candidate_id ON matching_cache(candidate_id);
CREATE INDEX IF NOT EXISTS idx_matching_score ON matching_cache(match_score);
CREATE INDEX IF NOT EXISTS idx_matching_created_at ON matching_cache(created_at);

-- Audit logs indexes
CREATE INDEX IF NOT EXISTS idx_audit_user_id ON audit_logs(user_id);
CREATE INDEX IF NOT EXISTS idx_audit_client_id ON audit_logs(client_id);
CREATE INDEX IF NOT EXISTS idx_audit_action ON audit_logs(action);
CREATE INDEX IF NOT EXISTS idx_audit_timestamp ON audit_logs(timestamp);
CREATE INDEX IF NOT EXISTS idx_audit_ip_address ON audit_logs(ip_address);
CREATE INDEX IF NOT EXISTS idx_audit_success ON audit_logs(success);

-- Rate limits indexes
CREATE INDEX IF NOT EXISTS idx_rate_limits_ip_endpoint ON rate_limits(ip_address, endpoint);
CREATE INDEX IF NOT EXISTS idx_rate_limits_window_start ON rate_limits(window_start);

-- CSP violations indexes
CREATE INDEX IF NOT EXISTS idx_csp_violations_timestamp ON csp_violations(timestamp);
CREATE INDEX IF NOT EXISTS idx_csp_violations_ip ON csp_violations(ip_address);

-- Company scoring preferences indexes
CREATE INDEX IF NOT EXISTS idx_company_scoring_client ON company_scoring_preferences(client_id);

-- Job applications indexes
CREATE INDEX IF NOT EXISTS idx_job_applications_candidate ON job_applications(candidate_id);
CREATE INDEX IF NOT EXISTS idx_job_applications_job ON job_applications(job_id);
CREATE INDEX IF NOT EXISTS idx_job_applications_status ON job_applications(status);
CREATE INDEX IF NOT EXISTS idx_job_applications_date ON job_applications(applied_date);

-- Workflows table indexes
CREATE INDEX IF NOT EXISTS idx_workflows_workflow_id ON workflows(workflow_id);
CREATE INDEX IF NOT EXISTS idx_workflows_status ON workflows(status);
CREATE INDEX IF NOT EXISTS idx_workflows_type ON workflows(workflow_type);
CREATE INDEX IF NOT EXISTS idx_workflows_candidate ON workflows(candidate_id);
CREATE INDEX IF NOT EXISTS idx_workflows_job ON workflows(job_id);
CREATE INDEX IF NOT EXISTS idx_workflows_client ON workflows(client_id);
CREATE INDEX IF NOT EXISTS idx_workflows_started_at ON workflows(started_at);
CREATE INDEX IF NOT EXISTS idx_workflows_completed_at ON workflows(completed_at);

-- RL Tables indexes
CREATE INDEX IF NOT EXISTS idx_rl_predictions_candidate_job ON rl_predictions(candidate_id, job_id);
CREATE INDEX IF NOT EXISTS idx_rl_predictions_created ON rl_predictions(created_at);
CREATE INDEX IF NOT EXISTS idx_rl_feedback_prediction ON rl_feedback(prediction_id);
CREATE INDEX IF NOT EXISTS idx_rl_feedback_outcome ON rl_feedback(actual_outcome, created_at);
CREATE INDEX IF NOT EXISTS idx_rl_performance_version ON rl_model_performance(model_version);
CREATE INDEX IF NOT EXISTS idx_rl_training_batch ON rl_training_data(training_batch);

-- Enhanced matching cache with learning data
ALTER TABLE matching_cache ADD COLUMN IF NOT EXISTS learning_version VARCHAR(50) DEFAULT 'v3.0';

-- Add missing performance indexes that may not exist in production
CREATE INDEX IF NOT EXISTS idx_candidates_skills_gin ON candidates USING gin(to_tsvector('english', technical_skills));
CREATE INDEX IF NOT EXISTS idx_candidates_score ON candidates(average_score);
CREATE INDEX IF NOT EXISTS idx_users_2fa_enabled ON users(is_2fa_enabled);
CREATE INDEX IF NOT EXISTS idx_users_last_login ON users(last_login);
CREATE INDEX IF NOT EXISTS idx_clients_2fa_enabled ON clients(two_factor_enabled);

-- ============================================================================
-- TRIGGERS AND FUNCTIONS
-- ============================================================================

-- Update timestamp trigger function
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Apply update triggers
CREATE TRIGGER update_candidates_updated_at BEFORE UPDATE ON candidates FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_jobs_updated_at BEFORE UPDATE ON jobs FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_offers_updated_at BEFORE UPDATE ON offers FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_clients_updated_at BEFORE UPDATE ON clients FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Audit logging trigger function
CREATE OR REPLACE FUNCTION audit_table_changes()
RETURNS TRIGGER AS $$
BEGIN
    INSERT INTO audit_logs (action, resource, resource_id, details, timestamp)
    VALUES (
        TG_OP,
        TG_TABLE_NAME,
        COALESCE(NEW.id, OLD.id),
        jsonb_build_object(
            'old', to_jsonb(OLD),
            'new', to_jsonb(NEW)
        ),
        CURRENT_TIMESTAMP
    );
    RETURN COALESCE(NEW, OLD);
END;
$$ language 'plpgsql';

-- Apply update triggers
CREATE TRIGGER update_job_applications_updated_at BEFORE UPDATE ON job_applications FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_workflows_updated_at BEFORE UPDATE ON workflows FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Apply audit triggers to sensitive tables
CREATE TRIGGER audit_candidates_changes AFTER INSERT OR UPDATE OR DELETE ON candidates FOR EACH ROW EXECUTE FUNCTION audit_table_changes();
CREATE TRIGGER audit_jobs_changes AFTER INSERT OR UPDATE OR DELETE ON jobs FOR EACH ROW EXECUTE FUNCTION audit_table_changes();
CREATE TRIGGER audit_feedback_changes AFTER INSERT OR UPDATE OR DELETE ON feedback FOR EACH ROW EXECUTE FUNCTION audit_table_changes();
CREATE TRIGGER audit_users_changes AFTER INSERT OR UPDATE OR DELETE ON users FOR EACH ROW EXECUTE FUNCTION audit_table_changes();
CREATE TRIGGER audit_clients_changes AFTER INSERT OR UPDATE OR DELETE ON clients FOR EACH ROW EXECUTE FUNCTION audit_table_changes();
CREATE TRIGGER audit_job_applications_changes AFTER INSERT OR UPDATE OR DELETE ON job_applications FOR EACH ROW EXECUTE FUNCTION audit_table_changes();
CREATE TRIGGER audit_workflows_changes AFTER INSERT OR UPDATE OR DELETE ON workflows FOR EACH ROW EXECUTE FUNCTION audit_table_changes();

-- ============================================================================
-- SAMPLE DATA FOR TESTING
-- ============================================================================

-- Insert sample jobs
INSERT INTO jobs (title, department, location, experience_level, requirements, description, client_id, employment_type) VALUES
('Senior Python Developer', 'Engineering', 'Remote', 'Senior', 'Python, Django, PostgreSQL, REST APIs, 5+ years experience', 'We are looking for a senior Python developer to join our engineering team and build scalable web applications.', 'TECH001', 'Full-time'),
('Data Scientist', 'Analytics', 'New York', 'Mid', 'Python, Machine Learning, SQL, Statistics, 3+ years experience', 'Join our data science team to build predictive models and extract insights from large datasets.', 'TECH001', 'Full-time'),
('Frontend Developer', 'Engineering', 'San Francisco', 'Junior', 'React, JavaScript, HTML/CSS, TypeScript, 2+ years experience', 'Build amazing user interfaces with React and modern frontend technologies.', 'STARTUP01', 'Full-time'),
('DevOps Engineer', 'Infrastructure', 'Austin', 'Senior', 'AWS, Docker, Kubernetes, CI/CD, Terraform, 4+ years experience', 'Manage our cloud infrastructure and deployment pipelines using modern DevOps practices.', 'ENTERPRISE01', 'Full-time'),
('Product Manager', 'Product', 'Seattle', 'Mid', 'Product strategy, Analytics, Agile, Stakeholder management, 3+ years experience', 'Lead product development and strategy initiatives for our core platform.', 'TECH001', 'Full-time')
ON CONFLICT DO NOTHING;

-- Insert sample clients
INSERT INTO clients (client_id, client_name, company_name, password_hash, email, status) VALUES
('TECH001', 'Tech Innovations Inc', 'Tech Innovations Inc', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj3bp.gSInG2', 'contact@techinnovations.com', 'active'),
('STARTUP01', 'Startup Ventures', 'Startup Ventures LLC', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj3bp.gSInG2', 'hello@startupventures.com', 'active'),
('ENTERPRISE01', 'Enterprise Solutions', 'Enterprise Solutions Corp', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj3bp.gSInG2', 'admin@enterprisesolutions.com', 'active')
ON CONFLICT (client_id) DO NOTHING;

-- Insert sample users
INSERT INTO users (username, email, password_hash, role, is_2fa_enabled) VALUES
('admin', 'admin@bhiv.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj3bp.gSInG2', 'admin', FALSE),
('hr_manager', 'hr@bhiv.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj3bp.gSInG2', 'hr_manager', FALSE),
('recruiter', 'recruiter@bhiv.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj3bp.gSInG2', 'recruiter', FALSE)
ON CONFLICT (username) DO NOTHING;

-- Note: Generated columns (average_score in feedback table) are automatically calculated
-- No manual updates needed for generated columns

-- Update existing candidates with calculated average scores from feedback
UPDATE candidates 
SET average_score = (
    SELECT AVG((integrity + honesty + discipline + hard_work + gratitude) / 5.0)
    FROM feedback 
    WHERE feedback.candidate_id = candidates.id
)
WHERE id IN (SELECT DISTINCT candidate_id FROM feedback WHERE integrity IS NOT NULL);

-- Schema version tracking
CREATE TABLE IF NOT EXISTS schema_version (
    version VARCHAR(20) PRIMARY KEY,
    applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    description TEXT
);

INSERT INTO schema_version (version, description) VALUES 
('4.3.0', 'Added RL + Feedback Agent tables (Ishan integration) - December 4, 2025'),
('4.2.2', 'Added workflows table for LangGraph workflow tracking - November 15, 2025'),
('4.2.1', 'Complete consolidated schema with all missing components - November 11, 2025'),
('4.2.0', 'Production schema with job_applications table and client auth fixes - November 4, 2025'),
('4.1.0', 'Production consolidated schema with Phase 3 learning engine'),
('4.0.1', 'Fixed schema - removed invalid generated column update'),
('3.0.0', 'Phase 3 - Learning engine and enhanced batch processing')
ON CONFLICT (version) DO UPDATE SET applied_at = CURRENT_TIMESTAMP;

-- Initialize RL model performance record
INSERT INTO rl_model_performance (
    model_version, accuracy, precision_score, recall_score, f1_score, 
    average_reward, total_predictions, evaluation_date
) VALUES (
    'v1.0.0', 0.0, 0.0, 0.0, 0.0, 0.0, 0, CURRENT_TIMESTAMP
) ON CONFLICT DO NOTHING;

-- Final success message
SELECT 'BHIV HR Platform Consolidated Schema v4.3.0 - Successfully Applied with RL + Feedback Agent Integration' as status;

-- ============================================================================
-- PRODUCTION SYNC VERIFICATION
-- ============================================================================

-- Verify all required extensions are installed
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_extension WHERE extname = 'uuid-ossp') THEN
        RAISE NOTICE 'Extension uuid-ossp is missing - will be created';
    END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_extension WHERE extname = 'pg_trgm') THEN
        RAISE NOTICE 'Extension pg_trgm is missing - will be created';
    END IF;
END $$;

-- Verify all required columns exist in clients table
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'clients' AND column_name = 'two_factor_enabled') THEN
        RAISE NOTICE 'Column clients.two_factor_enabled is missing - will be added';
    END IF;
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'clients' AND column_name = 'backup_codes') THEN
        RAISE NOTICE 'Column clients.backup_codes is missing - will be added';
    END IF;
END $$;

-- Show completion status
SELECT 
    'Schema v4.2.1 Ready for Production Deployment' as status,
    COUNT(*) as total_tables
FROM information_schema.tables 
WHERE table_schema = 'public' AND table_type = 'BASE TABLE';