-- =====================================================
-- COMPLETE SUPABASE SETUP FOR GURUKUL APPLICATION
-- =====================================================
-- Run this entire script in your Supabase SQL Editor
-- This will set up all necessary tables, indexes, and sample data

-- =====================================================
-- 1. CREATE STUDENTS TABLE
-- =====================================================

-- Drop existing students table if it exists (to ensure correct schema)
DROP TABLE IF EXISTS students CASCADE;

-- Create students table for storing student intake data
CREATE TABLE students (
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
CREATE POLICY "Allow all operations for authenticated users on students" ON students
  FOR ALL USING (true);

-- =====================================================
-- 2. CREATE FORM CONFIGURATIONS TABLE
-- =====================================================

-- Create form_configurations table for storing dynamic form configurations
CREATE TABLE IF NOT EXISTS form_configurations (
  id TEXT PRIMARY KEY,
  name TEXT NOT NULL,
  description TEXT,
  fields JSONB NOT NULL DEFAULT '[]'::jsonb,
  is_active BOOLEAN DEFAULT false,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Create indexes for faster queries
CREATE INDEX IF NOT EXISTS idx_form_configurations_active ON form_configurations(is_active);
CREATE INDEX IF NOT EXISTS idx_form_configurations_updated_at ON form_configurations(updated_at);

-- Enable Row Level Security (RLS)
ALTER TABLE form_configurations ENABLE ROW LEVEL SECURITY;

-- Create policy to allow all operations for authenticated users
CREATE POLICY "Allow all operations for authenticated users on form_configurations" ON form_configurations
  FOR ALL USING (true);

-- =====================================================
-- 3. CREATE UPDATE TIMESTAMP FUNCTIONS AND TRIGGERS
-- =====================================================

-- Function to automatically update the updated_at timestamp for students
CREATE OR REPLACE FUNCTION update_students_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Function to automatically update the updated_at timestamp for form_configurations
CREATE OR REPLACE FUNCTION update_form_configurations_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Create triggers to automatically update updated_at
CREATE TRIGGER update_students_updated_at 
    BEFORE UPDATE ON students 
    FOR EACH ROW 
    EXECUTE FUNCTION update_students_updated_at_column();

CREATE TRIGGER update_form_configurations_updated_at 
    BEFORE UPDATE ON form_configurations 
    FOR EACH ROW 
    EXECUTE FUNCTION update_form_configurations_updated_at_column();

-- =====================================================
-- 4. INSERT DEFAULT FORM CONFIGURATION
-- =====================================================

-- Insert default form configuration that matches the current intake form
INSERT INTO form_configurations (
  id,
  name,
  description,
  fields,
  is_active,
  created_at,
  updated_at
) VALUES (
  'default_config',
  'Default Student Intake Form',
  'Default form configuration matching the original intake form',
  '[
    {
      "id": "name",
      "type": "text",
      "label": "Full Name",
      "placeholder": "e.g., Asha Gupta",
      "required": true,
      "order": 1,
      "validation": {
        "minLength": 2,
        "maxLength": 100
      }
    },
    {
      "id": "age",
      "type": "number",
      "label": "Age",
      "placeholder": "17",
      "required": false,
      "order": 2,
      "validation": {
        "min": 5,
        "max": 100
      }
    },
    {
      "id": "email",
      "type": "email",
      "label": "Email",
      "placeholder": "your.email@example.com",
      "required": false,
      "order": 3,
      "validation": {
        "pattern": "^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\\\.[a-zA-Z]{2,}$"
      }
    },
    {
      "id": "phone",
      "type": "text",
      "label": "Phone",
      "placeholder": "999-000-1234",
      "required": false,
      "order": 4,
      "validation": {
        "pattern": "^[\\\\d\\\\s\\\\-\\\\+\\\\(\\\\)]+$"
      }
    },
    {
      "id": "education_level",
      "type": "select",
      "label": "Education Level",
      "placeholder": "Select your education level",
      "required": false,
      "order": 5,
      "options": [
        { "value": "high_school", "label": "High School" },
        { "value": "undergraduate", "label": "Undergraduate" },
        { "value": "graduate", "label": "Graduate" },
        { "value": "postgraduate", "label": "Postgraduate" },
        { "value": "other", "label": "Other" }
      ]
    },
    {
      "id": "field_of_study",
      "type": "text",
      "label": "Field of Study",
      "placeholder": "CS, Math, Humanities, ...",
      "required": false,
      "order": 6
    },
    {
      "id": "current_skills",
      "type": "textarea",
      "label": "Current Skills (comma separated)",
      "placeholder": "JavaScript, Algebra, Writing",
      "required": false,
      "order": 7,
      "helpText": "Example: JavaScript, Algebra, Writing"
    },
    {
      "id": "interests",
      "type": "textarea",
      "label": "Interests (comma separated)",
      "placeholder": "Programming, Mathematics, Art",
      "required": false,
      "order": 8,
      "helpText": "Example: Programming, Mathematics, Art"
    },
    {
      "id": "goals",
      "type": "textarea",
      "label": "Goals",
      "placeholder": "What do you want to achieve?",
      "required": false,
      "order": 9
    },
    {
      "id": "preferred_learning_style",
      "type": "radio",
      "label": "Preferred Learning Style",
      "required": false,
      "order": 10,
      "options": [
        { "value": "video", "label": "Video" },
        { "value": "text", "label": "Text" },
        { "value": "interactive", "label": "Interactive" },
        { "value": "mixed", "label": "Mixed" }
      ]
    },
    {
      "id": "availability_per_week_hours",
      "type": "number",
      "label": "Availability per week (hours)",
      "placeholder": "6",
      "required": false,
      "order": 11,
      "validation": {
        "min": 0,
        "max": 168
      }
    },
    {
      "id": "experience_years",
      "type": "number",
      "label": "Prior experience (years)",
      "placeholder": "0",
      "required": false,
      "order": 12,
      "validation": {
        "min": 0,
        "max": 50
      }
    }
  ]'::jsonb,
  true,
  NOW(),
  NOW()
) ON CONFLICT (id) DO UPDATE SET
  fields = EXCLUDED.fields,
  is_active = EXCLUDED.is_active,
  updated_at = NOW();

-- =====================================================
-- 5. INSERT SAMPLE STUDENT DATA (OPTIONAL)
-- =====================================================

-- Insert sample students for testing
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

-- =====================================================
-- 6. VERIFICATION QUERIES (OPTIONAL)
-- =====================================================

-- Uncomment these to verify your setup worked correctly:

-- Check if tables were created
-- SELECT table_name FROM information_schema.tables WHERE table_schema = 'public';

-- Check students table
-- SELECT * FROM students;

-- Check form configurations
-- SELECT id, name, is_active, created_at FROM form_configurations;

-- Check active form configuration
-- SELECT * FROM form_configurations WHERE is_active = true;

-- =====================================================
-- SETUP COMPLETE!
-- =====================================================
-- Your Supabase database is now ready for the Gurukul application.
-- Make sure to set up your environment variables:
-- VITE_SUPABASE_URL=your_supabase_url
-- VITE_SUPABASE_ANON_KEY=your_supabase_anon_key
-- VITE_SUPABASE_TABLE=students
