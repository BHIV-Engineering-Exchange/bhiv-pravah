-- Fix RLS Policies for Assignment System
-- Run this script in Supabase SQL Editor to fix Row Level Security policies

-- First, let's ensure the tables exist with proper structure
-- Create students table if it doesn't exist
CREATE TABLE IF NOT EXISTS students (
    id BIGSERIAL PRIMARY KEY,
    user_id TEXT NOT NULL UNIQUE,
    name TEXT NOT NULL,
    email TEXT,
    student_id TEXT UNIQUE,
    responses JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create assignment_attempts table if it doesn't exist
CREATE TABLE IF NOT EXISTS assignment_attempts (
    id BIGSERIAL PRIMARY KEY,
    user_id TEXT NOT NULL,
    student_id BIGINT REFERENCES students(id),
    user_email TEXT,
    assignment_id TEXT,
    started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    time_taken_seconds INTEGER,
    total_score DECIMAL(10,2),
    max_score DECIMAL(10,2),
    percentage DECIMAL(5,2),
    grade TEXT,
    category_scores JSONB,
    overall_feedback TEXT,
    strengths JSONB,
    improvement_areas JSONB,
    auto_submitted BOOLEAN DEFAULT FALSE,
    evaluated_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create assignment_responses table if it doesn't exist
CREATE TABLE IF NOT EXISTS assignment_responses (
    id BIGSERIAL PRIMARY KEY,
    attempt_id BIGINT NOT NULL REFERENCES assignment_attempts(id) ON DELETE CASCADE,
    question_id TEXT NOT NULL,
    question_category TEXT,
    question_difficulty TEXT,
    user_answer TEXT,
    user_explanation TEXT,
    correct_answer TEXT,
    is_correct BOOLEAN,
    accuracy_score DECIMAL(4,2),
    explanation_score DECIMAL(4,2),
    reasoning_score DECIMAL(4,2),
    total_score DECIMAL(4,2),
    max_score DECIMAL(4,2),
    ai_feedback TEXT,
    suggestions TEXT,
    evaluated_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Enable RLS on all tables
ALTER TABLE students ENABLE ROW LEVEL SECURITY;
ALTER TABLE assignment_attempts ENABLE ROW LEVEL SECURITY;
ALTER TABLE assignment_responses ENABLE ROW LEVEL SECURITY;

-- Drop existing policies if they exist
DROP POLICY IF EXISTS "Users can view their own student record" ON students;
DROP POLICY IF EXISTS "Users can insert their own student record" ON students;
DROP POLICY IF EXISTS "Users can update their own student record" ON students;

DROP POLICY IF EXISTS "Users can view their own assignment attempts" ON assignment_attempts;
DROP POLICY IF EXISTS "Users can insert their own assignment attempts" ON assignment_attempts;
DROP POLICY IF EXISTS "Users can update their own assignment attempts" ON assignment_attempts;

DROP POLICY IF EXISTS "Users can view their own assignment responses" ON assignment_responses;
DROP POLICY IF EXISTS "Users can insert their own assignment responses" ON assignment_responses;

-- Create RLS policies for students table
CREATE POLICY "Users can view their own student record" ON students
    FOR SELECT USING (auth.uid()::text = user_id);

CREATE POLICY "Users can insert their own student record" ON students
    FOR INSERT WITH CHECK (auth.uid()::text = user_id);

CREATE POLICY "Users can update their own student record" ON students
    FOR UPDATE USING (auth.uid()::text = user_id);

-- Create RLS policies for assignment_attempts table
CREATE POLICY "Users can view their own assignment attempts" ON assignment_attempts
    FOR SELECT USING (auth.uid()::text = user_id);

CREATE POLICY "Users can insert their own assignment attempts" ON assignment_attempts
    FOR INSERT WITH CHECK (auth.uid()::text = user_id);

CREATE POLICY "Users can update their own assignment attempts" ON assignment_attempts
    FOR UPDATE USING (auth.uid()::text = user_id);

-- Create RLS policies for assignment_responses table
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

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_students_user_id ON students(user_id);
CREATE INDEX IF NOT EXISTS idx_assignment_attempts_user_id ON assignment_attempts(user_id);
CREATE INDEX IF NOT EXISTS idx_assignment_attempts_student_id ON assignment_attempts(student_id);
CREATE INDEX IF NOT EXISTS idx_assignment_responses_attempt_id ON assignment_responses(attempt_id);

-- Create updated_at trigger function if it doesn't exist
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Create triggers for updated_at columns
DROP TRIGGER IF EXISTS update_students_updated_at ON students;
CREATE TRIGGER update_students_updated_at 
    BEFORE UPDATE ON students 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS update_assignment_attempts_updated_at ON assignment_attempts;
CREATE TRIGGER update_assignment_attempts_updated_at 
    BEFORE UPDATE ON assignment_attempts 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Grant necessary permissions (if using service role)
-- Note: These might not be needed if using the default setup
-- GRANT ALL ON students TO authenticated;
-- GRANT ALL ON assignment_attempts TO authenticated;
-- GRANT ALL ON assignment_responses TO authenticated;

-- Test the policies by checking if they exist
SELECT schemaname, tablename, policyname, permissive, roles, cmd, qual 
FROM pg_policies 
WHERE tablename IN ('students', 'assignment_attempts', 'assignment_responses')
ORDER BY tablename, policyname;

-- Display success message
SELECT 'RLS policies have been successfully created/updated for assignment system tables' as status;
