-- SQL script to create assignment-related tables in Supabase

-- Create assignment_attempts table (integrates with existing students table)
CREATE TABLE IF NOT EXISTS assignment_attempts (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id TEXT NOT NULL,
    student_id UUID REFERENCES students(id) ON DELETE CASCADE,
    user_email TEXT,
    assignment_id TEXT NOT NULL,
    started_at TIMESTAMPTZ NOT NULL,
    completed_at TIMESTAMPTZ NOT NULL,
    time_taken_seconds INTEGER NOT NULL,
    total_score DECIMAL(5,2) NOT NULL,
    max_score DECIMAL(5,2) NOT NULL,
    percentage DECIMAL(5,2) NOT NULL,
    grade TEXT NOT NULL,
    category_scores JSONB NOT NULL DEFAULT '{}',
    overall_feedback TEXT,
    strengths JSONB DEFAULT '[]',
    improvement_areas JSONB DEFAULT '[]',
    auto_submitted BOOLEAN DEFAULT FALSE,
    evaluated_at TIMESTAMPTZ NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Create assignment_responses table for detailed question responses
CREATE TABLE IF NOT EXISTS assignment_responses (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    attempt_id UUID REFERENCES assignment_attempts(id) ON DELETE CASCADE,
    question_id TEXT NOT NULL,
    question_category TEXT NOT NULL,
    question_difficulty TEXT NOT NULL,
    user_answer TEXT,
    user_explanation TEXT,
    correct_answer TEXT NOT NULL,
    is_correct BOOLEAN NOT NULL,
    accuracy_score DECIMAL(4,2) NOT NULL,
    explanation_score DECIMAL(4,2) NOT NULL,
    reasoning_score DECIMAL(4,2) NOT NULL,
    total_score DECIMAL(4,2) NOT NULL,
    max_score DECIMAL(4,2) NOT NULL DEFAULT 10.00,
    ai_feedback TEXT,
    suggestions TEXT,
    evaluated_at TIMESTAMPTZ NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_assignment_attempts_user_id ON assignment_attempts(user_id);
CREATE INDEX IF NOT EXISTS idx_assignment_attempts_user_email ON assignment_attempts(user_email);
CREATE INDEX IF NOT EXISTS idx_assignment_attempts_created_at ON assignment_attempts(created_at);
CREATE INDEX IF NOT EXISTS idx_assignment_attempts_percentage ON assignment_attempts(percentage);
CREATE INDEX IF NOT EXISTS idx_assignment_responses_attempt_id ON assignment_responses(attempt_id);
CREATE INDEX IF NOT EXISTS idx_assignment_responses_category ON assignment_responses(question_category);
CREATE INDEX IF NOT EXISTS idx_assignment_responses_is_correct ON assignment_responses(is_correct);

-- Create GIN index for JSONB columns for efficient querying
CREATE INDEX IF NOT EXISTS idx_assignment_attempts_category_scores ON assignment_attempts USING GIN (category_scores);
CREATE INDEX IF NOT EXISTS idx_assignment_attempts_strengths ON assignment_attempts USING GIN (strengths);
CREATE INDEX IF NOT EXISTS idx_assignment_attempts_improvement_areas ON assignment_attempts USING GIN (improvement_areas);

-- Enable Row Level Security
ALTER TABLE assignment_attempts ENABLE ROW LEVEL SECURITY;
ALTER TABLE assignment_responses ENABLE ROW LEVEL SECURITY;

-- Create RLS policies for assignment_attempts
CREATE POLICY "Users can view their own assignment attempts" ON assignment_attempts
    FOR SELECT USING (auth.uid()::text = user_id);

CREATE POLICY "Users can insert their own assignment attempts" ON assignment_attempts
    FOR INSERT WITH CHECK (auth.uid()::text = user_id);

CREATE POLICY "Users can update their own assignment attempts" ON assignment_attempts
    FOR UPDATE USING (auth.uid()::text = user_id);

-- Create RLS policies for assignment_responses
CREATE POLICY "Users can view their own assignment responses" ON assignment_responses
    FOR SELECT USING (
        EXISTS (
            SELECT 1 FROM assignment_attempts 
            WHERE assignment_attempts.id = assignment_responses.attempt_id 
            AND assignment_attempts.user_id = auth.uid()::text
        )
    );

CREATE POLICY "Users can insert their own assignment responses" ON assignment_responses
    FOR INSERT WITH CHECK (
        EXISTS (
            SELECT 1 FROM assignment_attempts 
            WHERE assignment_attempts.id = assignment_responses.attempt_id 
            AND assignment_attempts.user_id = auth.uid()::text
        )
    );

-- Create function to automatically update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Create trigger for assignment_attempts
CREATE TRIGGER update_assignment_attempts_updated_at 
    BEFORE UPDATE ON assignment_attempts 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Create view for assignment statistics
CREATE OR REPLACE VIEW assignment_stats AS
SELECT 
    user_id,
    user_email,
    COUNT(*) as total_attempts,
    AVG(percentage) as avg_percentage,
    MAX(percentage) as best_percentage,
    MIN(percentage) as worst_percentage,
    AVG(time_taken_seconds) as avg_time_taken,
    COUNT(CASE WHEN grade = 'A' THEN 1 END) as grade_a_count,
    COUNT(CASE WHEN grade = 'B' THEN 1 END) as grade_b_count,
    COUNT(CASE WHEN grade = 'C' THEN 1 END) as grade_c_count,
    COUNT(CASE WHEN grade = 'D' THEN 1 END) as grade_d_count,
    COUNT(CASE WHEN grade = 'F' THEN 1 END) as grade_f_count,
    MAX(created_at) as last_attempt_date,
    MIN(created_at) as first_attempt_date
FROM assignment_attempts
GROUP BY user_id, user_email;

-- Create view for category performance analysis
CREATE OR REPLACE VIEW category_performance AS
SELECT 
    ar.question_category,
    COUNT(*) as total_questions,
    COUNT(CASE WHEN ar.is_correct THEN 1 END) as correct_answers,
    AVG(ar.accuracy_score) as avg_accuracy_score,
    AVG(ar.explanation_score) as avg_explanation_score,
    AVG(ar.reasoning_score) as avg_reasoning_score,
    AVG(ar.total_score) as avg_total_score,
    ROUND((COUNT(CASE WHEN ar.is_correct THEN 1 END)::DECIMAL / COUNT(*)) * 100, 2) as accuracy_percentage
FROM assignment_responses ar
JOIN assignment_attempts aa ON ar.attempt_id = aa.id
GROUP BY ar.question_category;

-- Grant necessary permissions (adjust based on your Supabase setup)
-- These might need to be adjusted based on your specific Supabase configuration

-- Comments for documentation
COMMENT ON TABLE assignment_attempts IS 'Stores completed assignment attempts with overall scores and feedback';
COMMENT ON TABLE assignment_responses IS 'Stores detailed responses for each question in an assignment attempt';
COMMENT ON VIEW assignment_stats IS 'Provides statistical overview of user assignment performance';
COMMENT ON VIEW category_performance IS 'Analyzes performance across different question categories';

-- Success message
SELECT 'Assignment tables created successfully!' as status;
