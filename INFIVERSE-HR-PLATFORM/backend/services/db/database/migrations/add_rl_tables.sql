-- RL Tables Migration for BHIV HR Platform
-- Adds Reinforcement Learning and Feedback tables to existing PostgreSQL schema

-- RL Predictions & Scoring
CREATE TABLE IF NOT EXISTS rl_predictions (
    id SERIAL PRIMARY KEY,
    candidate_id INTEGER NOT NULL,
    job_id INTEGER NOT NULL,
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

-- Performance Indexes
CREATE INDEX IF NOT EXISTS idx_rl_predictions_candidate_job ON rl_predictions(candidate_id, job_id);
CREATE INDEX IF NOT EXISTS idx_rl_predictions_created ON rl_predictions(created_at);
CREATE INDEX IF NOT EXISTS idx_rl_feedback_prediction ON rl_feedback(prediction_id);
CREATE INDEX IF NOT EXISTS idx_rl_feedback_outcome ON rl_feedback(actual_outcome, created_at);
CREATE INDEX IF NOT EXISTS idx_rl_performance_version ON rl_model_performance(model_version);
CREATE INDEX IF NOT EXISTS idx_rl_training_batch ON rl_training_data(training_batch);

-- Insert initial model performance record
INSERT INTO rl_model_performance (
    model_version, accuracy, precision_score, recall_score, f1_score, 
    average_reward, total_predictions, evaluation_date
) VALUES (
    'v1.0.0', 0.0, 0.0, 0.0, 0.0, 0.0, 0, CURRENT_TIMESTAMP
) ON CONFLICT DO NOTHING;