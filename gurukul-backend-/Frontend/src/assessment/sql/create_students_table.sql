-- Create students table for storing student intake data
CREATE TABLE IF NOT EXISTS students (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id TEXT,
  name TEXT,
  email TEXT UNIQUE,
  student_id TEXT,
  grade TEXT,
  tier TEXT CHECK (tier IN ('Seed', 'Tree', 'Sky')),
  responses JSONB DEFAULT '{}'::jsonb,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_students_email ON students(email);
CREATE INDEX IF NOT EXISTS idx_students_user_id ON students(user_id);
CREATE INDEX IF NOT EXISTS idx_students_tier ON students(tier);
CREATE INDEX IF NOT EXISTS idx_students_created_at ON students(created_at);
CREATE INDEX IF NOT EXISTS idx_students_updated_at ON students(updated_at);

-- Create GIN index for JSONB responses field for efficient querying
CREATE INDEX IF NOT EXISTS idx_students_responses ON students USING GIN (responses);

-- Enable Row Level Security (RLS)
ALTER TABLE students ENABLE ROW LEVEL SECURITY;

-- Create policy to allow all operations for authenticated users
-- You can customize this based on your security requirements
CREATE POLICY "Allow all operations for authenticated users" ON students
  FOR ALL USING (true);

-- Create a function to automatically update the updated_at timestamp
CREATE OR REPLACE FUNCTION update_students_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Create trigger to automatically update updated_at
CREATE TRIGGER update_students_updated_at 
    BEFORE UPDATE ON students 
    FOR EACH ROW 
    EXECUTE FUNCTION update_students_updated_at_column();

-- Insert some sample data for testing (optional)
INSERT INTO students (
  name,
  email,
  student_id,
  grade,
  tier,
  responses,
  created_at,
  updated_at
) VALUES 
(
  'Asha Gupta',
  'asha.gupta@example.com',
  'STU001',
  '12th',
  'Seed',
  '{
    "age": 17,
    "phone": "999-000-1234",
    "education_level": "high_school",
    "field_of_study": "Computer Science",
    "current_skills": ["JavaScript", "HTML", "CSS"],
    "interests": ["Programming", "Mathematics", "AI"],
    "goals": "Learn advanced programming and AI concepts",
    "preferred_learning_style": "interactive",
    "availability_per_week_hours": 10,
    "experience_years": 1
  }'::jsonb,
  NOW(),
  NOW()
),
(
  'Raj Sharma',
  'raj.sharma@example.com',
  'STU002',
  'Undergraduate',
  'Tree',
  '{
    "age": 20,
    "phone": "888-111-2345",
    "education_level": "undergraduate",
    "field_of_study": "Mathematics",
    "current_skills": ["Python", "Calculus", "Statistics"],
    "interests": ["Data Science", "Machine Learning", "Research"],
    "goals": "Master data science and machine learning",
    "preferred_learning_style": "mixed",
    "availability_per_week_hours": 15,
    "experience_years": 2
  }'::jsonb,
  NOW(),
  NOW()
),
(
  'Priya Patel',
  'priya.patel@example.com',
  'STU003',
  'Graduate',
  'Sky',
  '{
    "age": 24,
    "phone": "777-222-3456",
    "education_level": "graduate",
    "field_of_study": "Computer Engineering",
    "current_skills": ["React", "Node.js", "Machine Learning", "Deep Learning"],
    "interests": ["AI Research", "Neural Networks", "Computer Vision"],
    "goals": "Contribute to cutting-edge AI research and development",
    "preferred_learning_style": "text",
    "availability_per_week_hours": 20,
    "experience_years": 4
  }'::jsonb,
  NOW(),
  NOW()
) ON CONFLICT (email) DO NOTHING;
