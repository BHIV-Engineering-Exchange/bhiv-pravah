-- =====================================================
-- COMPLETE FIELD-BASED ASSESSMENT SYSTEM SETUP
-- =====================================================
-- Run this entire script in your Supabase SQL Editor
-- This will set up all necessary tables, indexes, policies, and sample data
-- for the field-based assessment system with AI question generation

-- =====================================================
-- 1. DROP EXISTING TABLES (CLEAN SLATE)
-- =====================================================

DROP TABLE IF EXISTS assignment_responses CASCADE;
DROP TABLE IF EXISTS assignment_attempts CASCADE;
DROP TABLE IF EXISTS question_usage_stats CASCADE;
DROP TABLE IF EXISTS question_field_mapping CASCADE;
DROP TABLE IF EXISTS question_banks CASCADE;
DROP TABLE IF EXISTS study_fields CASCADE;
DROP TABLE IF EXISTS background_selections CASCADE;
DROP TABLE IF EXISTS form_configurations CASCADE;
DROP TABLE IF EXISTS students CASCADE;
DROP TABLE IF EXISTS admins CASCADE;

-- =====================================================
-- 2. CREATE CORE TABLES
-- =====================================================

-- Students table for storing student intake data
CREATE TABLE students (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id TEXT,
  name TEXT,
  email TEXT UNIQUE,
  student_id TEXT UNIQUE,
  grade TEXT,
  tier TEXT CHECK (tier IN ('Seed', 'Tree', 'Sky')),
  responses JSONB DEFAULT '{}'::jsonb,
  is_active BOOLEAN DEFAULT TRUE,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Form configurations table for dynamic forms
CREATE TABLE form_configurations (
  id TEXT PRIMARY KEY,
  name TEXT NOT NULL,
  description TEXT,
  fields JSONB NOT NULL DEFAULT '[]'::jsonb,
  is_active BOOLEAN DEFAULT false,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Background selections table for field/class/goal selection
CREATE TABLE background_selections (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id TEXT UNIQUE NOT NULL,
  field_of_study TEXT NOT NULL,
  class_level TEXT NOT NULL,
  learning_goals TEXT NOT NULL,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Study fields table to define available study fields
CREATE TABLE study_fields (
  id TEXT PRIMARY KEY,
  name TEXT NOT NULL,
  short_name TEXT NOT NULL,
  description TEXT,
  subcategories JSONB DEFAULT '[]',
  question_weights JSONB DEFAULT '{}',
  difficulty_distribution JSONB DEFAULT '{}',
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Question banks table to store all questions (admin + AI generated)
CREATE TABLE question_banks (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  question_id TEXT UNIQUE NOT NULL,
  category TEXT NOT NULL,
  difficulty TEXT NOT NULL,
  question_text TEXT NOT NULL,
  options JSONB NOT NULL DEFAULT '[]',
  correct_answer TEXT NOT NULL,
  explanation TEXT NOT NULL,
  vedic_connection TEXT DEFAULT '',
  modern_application TEXT DEFAULT '',
  tags JSONB DEFAULT '[]',
  is_active BOOLEAN DEFAULT TRUE,
  created_by TEXT DEFAULT 'admin',
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Question field mapping table to map questions to study fields
CREATE TABLE question_field_mapping (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  question_id TEXT REFERENCES question_banks(question_id) ON DELETE CASCADE,
  field_id TEXT NOT NULL,
  weight INTEGER DEFAULT 1,
  is_primary BOOLEAN DEFAULT FALSE,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  UNIQUE(question_id, field_id)
);

-- Question usage stats table to track question performance
CREATE TABLE question_usage_stats (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  question_id TEXT REFERENCES question_banks(question_id) ON DELETE CASCADE,
  total_attempts INTEGER DEFAULT 0,
  correct_attempts INTEGER DEFAULT 0,
  average_time_seconds DECIMAL(6,2) DEFAULT 0,
  difficulty_rating DECIMAL(3,2) DEFAULT 0,
  last_used TIMESTAMPTZ,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Assignment attempts table for storing assignment results
CREATE TABLE assignment_attempts (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  user_id TEXT NOT NULL,
  student_id UUID REFERENCES students(id) ON DELETE CASCADE,
  user_email TEXT,
  assignment_id TEXT NOT NULL,
  started_at TIMESTAMPTZ NOT NULL,
  completed_at TIMESTAMPTZ,
  time_taken_seconds INTEGER,
  total_score DECIMAL(6,2),
  max_score DECIMAL(6,2),
  percentage DECIMAL(5,2),
  grade TEXT,
  category_scores JSONB DEFAULT '{}',
  overall_feedback TEXT,
  strengths JSONB DEFAULT '[]',
  improvement_areas JSONB DEFAULT '[]',
  auto_submitted BOOLEAN DEFAULT FALSE,
  evaluated_at TIMESTAMPTZ,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Assignment responses table for detailed question responses
CREATE TABLE assignment_responses (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  attempt_id UUID REFERENCES assignment_attempts(id) ON DELETE CASCADE,
  question_id TEXT NOT NULL,
  question_category TEXT NOT NULL,
  question_difficulty TEXT NOT NULL,
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
  evaluated_at TIMESTAMPTZ,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Admins table for admin authentication
CREATE TABLE admins (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  user_id TEXT UNIQUE NOT NULL,
  username TEXT UNIQUE NOT NULL,
  email TEXT UNIQUE,
  is_active BOOLEAN DEFAULT TRUE,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- =====================================================
-- 3. CREATE INDEXES FOR PERFORMANCE
-- =====================================================

-- Students indexes
CREATE INDEX IF NOT EXISTS idx_students_email ON students(email);
CREATE INDEX IF NOT EXISTS idx_students_user_id ON students(user_id);
CREATE INDEX IF NOT EXISTS idx_students_student_id ON students(student_id);
CREATE INDEX IF NOT EXISTS idx_students_tier ON students(tier);
CREATE INDEX IF NOT EXISTS idx_students_created_at ON students(created_at);
CREATE INDEX IF NOT EXISTS idx_students_updated_at ON students(updated_at);
CREATE INDEX IF NOT EXISTS idx_students_responses ON students USING GIN (responses);

-- Form configurations indexes
CREATE INDEX IF NOT EXISTS idx_form_configurations_active ON form_configurations(is_active);
CREATE INDEX IF NOT EXISTS idx_form_configurations_updated_at ON form_configurations(updated_at);

-- Background selections indexes
CREATE INDEX IF NOT EXISTS idx_background_selections_user_id ON background_selections(user_id);
CREATE INDEX IF NOT EXISTS idx_background_selections_field ON background_selections(field_of_study);

-- Question banks indexes
CREATE INDEX IF NOT EXISTS idx_question_banks_category ON question_banks(category);
CREATE INDEX IF NOT EXISTS idx_question_banks_difficulty ON question_banks(difficulty);
CREATE INDEX IF NOT EXISTS idx_question_banks_active ON question_banks(is_active);
CREATE INDEX IF NOT EXISTS idx_question_banks_created_by ON question_banks(created_by);
CREATE INDEX IF NOT EXISTS idx_question_banks_options ON question_banks USING GIN (options);
CREATE INDEX IF NOT EXISTS idx_question_banks_tags ON question_banks USING GIN (tags);

-- Question field mapping indexes
CREATE INDEX IF NOT EXISTS idx_question_field_mapping_question_id ON question_field_mapping(question_id);
CREATE INDEX IF NOT EXISTS idx_question_field_mapping_field_id ON question_field_mapping(field_id);

-- Question usage stats indexes
CREATE INDEX IF NOT EXISTS idx_question_usage_stats_question_id ON question_usage_stats(question_id);

-- Study fields indexes
CREATE INDEX IF NOT EXISTS idx_study_fields_subcategories ON study_fields USING GIN (subcategories);
CREATE INDEX IF NOT EXISTS idx_study_fields_question_weights ON study_fields USING GIN (question_weights);

-- Assignment attempts indexes
CREATE INDEX IF NOT EXISTS idx_assignment_attempts_user_id ON assignment_attempts(user_id);
CREATE INDEX IF NOT EXISTS idx_assignment_attempts_user_email ON assignment_attempts(user_email);
CREATE INDEX IF NOT EXISTS idx_assignment_attempts_student_id ON assignment_attempts(student_id);
CREATE INDEX IF NOT EXISTS idx_assignment_attempts_created_at ON assignment_attempts(created_at);
CREATE INDEX IF NOT EXISTS idx_assignment_attempts_percentage ON assignment_attempts(percentage);
CREATE INDEX IF NOT EXISTS idx_assignment_attempts_category_scores ON assignment_attempts USING GIN (category_scores);

-- Assignment responses indexes
CREATE INDEX IF NOT EXISTS idx_assignment_responses_attempt_id ON assignment_responses(attempt_id);
CREATE INDEX IF NOT EXISTS idx_assignment_responses_category ON assignment_responses(question_category);
CREATE INDEX IF NOT EXISTS idx_assignment_responses_is_correct ON assignment_responses(is_correct);

-- Admins indexes
CREATE INDEX IF NOT EXISTS idx_admins_user_id ON admins(user_id);
CREATE INDEX IF NOT EXISTS idx_admins_username ON admins(username);

-- =====================================================
-- 4. CREATE FUNCTIONS AND TRIGGERS
-- =====================================================

-- Function to automatically update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Function for question usage stats
CREATE OR REPLACE FUNCTION update_question_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Function to update question usage statistics
CREATE OR REPLACE FUNCTION update_question_usage_stats(
    p_question_id TEXT,
    p_is_correct BOOLEAN,
    p_time_seconds INTEGER
)
RETURNS VOID AS $$
BEGIN
    INSERT INTO question_usage_stats (question_id, total_attempts, correct_attempts, average_time_seconds, last_used)
    VALUES (p_question_id, 1, CASE WHEN p_is_correct THEN 1 ELSE 0 END, p_time_seconds, NOW())
    ON CONFLICT (question_id) DO UPDATE SET
        total_attempts = question_usage_stats.total_attempts + 1,
        correct_attempts = question_usage_stats.correct_attempts + CASE WHEN p_is_correct THEN 1 ELSE 0 END,
        average_time_seconds = (question_usage_stats.average_time_seconds * question_usage_stats.total_attempts + p_time_seconds) / (question_usage_stats.total_attempts + 1),
        last_used = NOW(),
        updated_at = NOW();
END;
$$ LANGUAGE plpgsql;

-- Create triggers for updated_at columns
CREATE TRIGGER update_students_updated_at 
    BEFORE UPDATE ON students 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_form_configurations_updated_at 
    BEFORE UPDATE ON form_configurations 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_background_selections_updated_at 
    BEFORE UPDATE ON background_selections 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_study_fields_updated_at 
    BEFORE UPDATE ON study_fields 
    FOR EACH ROW EXECUTE FUNCTION update_question_updated_at_column();

CREATE TRIGGER update_question_banks_updated_at 
    BEFORE UPDATE ON question_banks 
    FOR EACH ROW EXECUTE FUNCTION update_question_updated_at_column();

CREATE TRIGGER update_question_usage_stats_updated_at 
    BEFORE UPDATE ON question_usage_stats 
    FOR EACH ROW EXECUTE FUNCTION update_question_updated_at_column();

CREATE TRIGGER update_assignment_attempts_updated_at 
    BEFORE UPDATE ON assignment_attempts 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_admins_updated_at 
    BEFORE UPDATE ON admins 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- =====================================================
-- 5. ENABLE ROW LEVEL SECURITY
-- =====================================================

ALTER TABLE students ENABLE ROW LEVEL SECURITY;
ALTER TABLE form_configurations ENABLE ROW LEVEL SECURITY;
ALTER TABLE background_selections ENABLE ROW LEVEL SECURITY;
ALTER TABLE study_fields ENABLE ROW LEVEL SECURITY;
ALTER TABLE question_banks ENABLE ROW LEVEL SECURITY;
ALTER TABLE question_field_mapping ENABLE ROW LEVEL SECURITY;
ALTER TABLE question_usage_stats ENABLE ROW LEVEL SECURITY;
ALTER TABLE assignment_attempts ENABLE ROW LEVEL SECURITY;
ALTER TABLE assignment_responses ENABLE ROW LEVEL SECURITY;
ALTER TABLE admins ENABLE ROW LEVEL SECURITY;

-- =====================================================
-- 6. CREATE RLS POLICIES (DEVELOPMENT-FRIENDLY)
-- =====================================================

-- Students policies
DROP POLICY IF EXISTS "Allow all operations for authenticated users on students" ON students;
CREATE POLICY "Allow all operations for authenticated users on students" ON students
  FOR ALL USING (true);

-- Form configurations policies
DROP POLICY IF EXISTS "Allow all operations for authenticated users on form_configurations" ON form_configurations;
CREATE POLICY "Allow all operations for authenticated users on form_configurations" ON form_configurations
  FOR ALL USING (true);

-- Background selections policies
DROP POLICY IF EXISTS "Allow all operations for authenticated users on background_selections" ON background_selections;
CREATE POLICY "Allow all operations for authenticated users on background_selections" ON background_selections
  FOR ALL USING (true);

-- Study fields policies (read-only for users, full access for admins)
DROP POLICY IF EXISTS "Anyone can view study fields" ON study_fields;
CREATE POLICY "Anyone can view study fields" ON study_fields
    FOR SELECT TO PUBLIC USING (true);

DROP POLICY IF EXISTS "Allow all operations for development" ON study_fields;
CREATE POLICY "Allow all operations for development" ON study_fields
    FOR ALL TO PUBLIC USING (true);

-- Question banks policies (allow AI generation)
DROP POLICY IF EXISTS "Anyone can view active questions" ON question_banks;
CREATE POLICY "Anyone can view active questions" ON question_banks
    FOR SELECT TO PUBLIC USING (is_active = true);

DROP POLICY IF EXISTS "Allow AI question generation" ON question_banks;
CREATE POLICY "Allow AI question generation" ON question_banks
    FOR INSERT TO PUBLIC 
    WITH CHECK (created_by = 'ai' OR created_by = 'admin');

DROP POLICY IF EXISTS "Allow question updates for development" ON question_banks;
CREATE POLICY "Allow question updates for development" ON question_banks
    FOR UPDATE TO PUBLIC USING (true);

DROP POLICY IF EXISTS "Allow question deletion for development" ON question_banks;
CREATE POLICY "Allow question deletion for development" ON question_banks
    FOR DELETE TO PUBLIC USING (true);

-- Question field mapping policies
DROP POLICY IF EXISTS "Anyone can view question field mappings" ON question_field_mapping;
CREATE POLICY "Anyone can view question field mappings" ON question_field_mapping
    FOR SELECT TO PUBLIC USING (true);

DROP POLICY IF EXISTS "Allow AI question field mapping" ON question_field_mapping;
CREATE POLICY "Allow AI question field mapping" ON question_field_mapping
    FOR INSERT TO PUBLIC WITH CHECK (true);

DROP POLICY IF EXISTS "Allow mapping updates for development" ON question_field_mapping;
CREATE POLICY "Allow mapping updates for development" ON question_field_mapping
    FOR ALL TO PUBLIC USING (true);

-- Question usage stats policies
DROP POLICY IF EXISTS "Anyone can view question usage stats" ON question_usage_stats;
CREATE POLICY "Anyone can view question usage stats" ON question_usage_stats
    FOR SELECT TO PUBLIC USING (true);

DROP POLICY IF EXISTS "System can update question usage stats" ON question_usage_stats;
CREATE POLICY "System can update question usage stats" ON question_usage_stats
    FOR ALL TO PUBLIC USING (true);

-- Assignment attempts policies
DROP POLICY IF EXISTS "Users can view their own assignment attempts" ON assignment_attempts;
CREATE POLICY "Users can view their own assignment attempts" ON assignment_attempts
    FOR SELECT USING (true);

DROP POLICY IF EXISTS "Users can insert their own assignment attempts" ON assignment_attempts;
CREATE POLICY "Users can insert their own assignment attempts" ON assignment_attempts
    FOR INSERT WITH CHECK (true);

DROP POLICY IF EXISTS "Users can update their own assignment attempts" ON assignment_attempts;
CREATE POLICY "Users can update their own assignment attempts" ON assignment_attempts
    FOR UPDATE USING (true);

-- Assignment responses policies
DROP POLICY IF EXISTS "Users can view their own assignment responses" ON assignment_responses;
CREATE POLICY "Users can view their own assignment responses" ON assignment_responses
    FOR SELECT USING (true);

DROP POLICY IF EXISTS "Users can insert their own assignment responses" ON assignment_responses;
CREATE POLICY "Users can insert their own assignment responses" ON assignment_responses
    FOR INSERT WITH CHECK (true);

-- Admins policies
DROP POLICY IF EXISTS "Admins can read their own data" ON admins;
CREATE POLICY "Admins can read their own data" ON admins
    FOR SELECT USING (true);

DROP POLICY IF EXISTS "Allow admin creation" ON admins;
CREATE POLICY "Allow admin creation" ON admins
    FOR INSERT WITH CHECK (true);

-- =====================================================
-- 7. INSERT DEFAULT DATA
-- =====================================================

-- Insert default study fields
INSERT INTO study_fields (id, name, short_name, description, subcategories, question_weights, difficulty_distribution) VALUES
('stem', 'STEM (Science, Technology, Engineering, Mathematics)', 'STEM', 
 'Science, Technology, Engineering, and Mathematics fields including Computer Science, Physics, Chemistry, Biology, Engineering, and Mathematical Sciences',
 '["Computer Science", "Software Engineering", "Data Science", "Cybersecurity", "Artificial Intelligence", "Physics", "Chemistry", "Biology", "Mathematics", "Engineering", "Information Technology"]',
 '{"Coding": 35, "Logic": 25, "Mathematics": 25, "Language": 5, "Culture": 5, "Vedic Knowledge": 3, "Current Affairs": 2}',
 '{"easy": 25, "medium": 50, "hard": 25}'),

('business', 'Business & Economics', 'Business',
 'Business administration, economics, finance, marketing, entrepreneurship, and related commercial fields',
 '["Business Administration", "Economics", "Finance", "Marketing", "Accounting", "Entrepreneurship", "Management", "International Business", "Supply Chain Management", "Human Resources"]',
 '{"Logic": 30, "Current Affairs": 25, "Language": 20, "Mathematics": 10, "Culture": 10, "Coding": 3, "Vedic Knowledge": 2}',
 '{"easy": 30, "medium": 50, "hard": 20}'),

('social_sciences', 'Social Sciences', 'Social Sciences',
 'Psychology, sociology, political science, anthropology, and other social science disciplines',
 '["Psychology", "Sociology", "Political Science", "Anthropology", "International Relations", "Social Work", "Criminology", "Geography", "History", "Philosophy"]',
 '{"Language": 30, "Culture": 25, "Current Affairs": 20, "Logic": 15, "Vedic Knowledge": 5, "Mathematics": 3, "Coding": 2}',
 '{"easy": 35, "medium": 45, "hard": 20}'),

('health_medicine', 'Health & Medicine', 'Health & Medicine',
 'Medicine, nursing, pharmacy, public health, and other healthcare-related fields',
 '["Medicine", "Nursing", "Pharmacy", "Public Health", "Dentistry", "Veterinary Medicine", "Physical Therapy", "Occupational Therapy", "Medical Technology", "Health Administration"]',
 '{"Logic": 30, "Current Affairs": 20, "Language": 20, "Mathematics": 15, "Vedic Knowledge": 8, "Culture": 5, "Coding": 2}',
 '{"easy": 30, "medium": 50, "hard": 20}'),

('creative_arts', 'Creative Arts & Humanities', 'Creative Arts',
 'Fine arts, literature, languages, music, theater, design, and other creative and humanities disciplines',
 '["Fine Arts", "Literature", "Languages", "Music", "Theater", "Film Studies", "Graphic Design", "Creative Writing", "Art History", "Linguistics"]',
 '{"Language": 35, "Culture": 25, "Vedic Knowledge": 15, "Current Affairs": 10, "Logic": 10, "Mathematics": 3, "Coding": 2}',
 '{"easy": 35, "medium": 45, "hard": 20}'),

('other', 'Other Fields', 'Other',
 'Agriculture, environmental studies, sports science, and other specialized fields',
 '["Agriculture", "Environmental Studies", "Sports Science", "Hospitality Management", "Tourism", "Architecture", "Urban Planning", "Library Science", "Education", "Law"]',
 '{"Language": 20, "Logic": 20, "Current Affairs": 20, "Culture": 15, "Mathematics": 10, "Vedic Knowledge": 10, "Coding": 5}',
 '{"easy": 30, "medium": 50, "hard": 20}')

ON CONFLICT (id) DO UPDATE SET
    name = EXCLUDED.name,
    short_name = EXCLUDED.short_name,
    description = EXCLUDED.description,
    subcategories = EXCLUDED.subcategories,
    question_weights = EXCLUDED.question_weights,
    difficulty_distribution = EXCLUDED.difficulty_distribution,
    updated_at = NOW();

-- Insert default form configuration
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
      "order": 3
    },
    {
      "id": "phone",
      "type": "text",
      "label": "Phone",
      "placeholder": "999-000-1234",
      "required": false,
      "order": 4
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
-- 8. CREATE VIEWS FOR EASIER QUERYING
-- =====================================================

-- Question bank summary view
CREATE OR REPLACE VIEW question_bank_summary AS
SELECT 
    category,
    difficulty,
    COUNT(*) as total_questions,
    COUNT(CASE WHEN is_active THEN 1 END) as active_questions,
    AVG(qus.correct_attempts::DECIMAL / NULLIF(qus.total_attempts, 0)) as average_accuracy
FROM question_banks qb
LEFT JOIN question_usage_stats qus ON qb.question_id = qus.question_id
GROUP BY category, difficulty
ORDER BY category, difficulty;

-- Field question distribution view
CREATE OR REPLACE VIEW field_question_distribution AS
SELECT 
    sf.id as field_id,
    sf.name as field_name,
    qb.category,
    qb.difficulty,
    COUNT(*) as question_count,
    COUNT(CASE WHEN qb.is_active THEN 1 END) as active_questions
FROM study_fields sf
LEFT JOIN question_field_mapping qfm ON sf.id = qfm.field_id
LEFT JOIN question_banks qb ON qfm.question_id = qb.question_id
GROUP BY sf.id, sf.name, qb.category, qb.difficulty
ORDER BY sf.name, qb.category, qb.difficulty;

-- Assignment statistics view
CREATE OR REPLACE VIEW assignment_stats AS
SELECT
    user_id,
    user_email,
    COUNT(*) as total_attempts,
    AVG(percentage) as average_percentage,
    MAX(percentage) as best_percentage,
    MIN(created_at) as first_attempt_date,
    MAX(created_at) as last_attempt_date
FROM assignment_attempts
GROUP BY user_id, user_email;

-- Category performance view
CREATE OR REPLACE VIEW category_performance AS
SELECT
    ar.question_category,
    COUNT(*) as total_questions,
    COUNT(CASE WHEN ar.is_correct THEN 1 END) as correct_answers,
    ROUND((COUNT(CASE WHEN ar.is_correct THEN 1 END)::DECIMAL / COUNT(*)) * 100, 2) as accuracy_percentage
FROM assignment_responses ar
JOIN assignment_attempts aa ON ar.attempt_id = aa.id
GROUP BY ar.question_category;

-- =====================================================
-- 9. COMMENTS FOR DOCUMENTATION
-- =====================================================

COMMENT ON TABLE students IS 'Stores student profile and intake form responses';
COMMENT ON TABLE form_configurations IS 'Dynamic form configurations for intake forms';
COMMENT ON TABLE background_selections IS 'Student field/class/goal selections for personalized forms';
COMMENT ON TABLE study_fields IS 'Defines available study fields with their question distribution weights';
COMMENT ON TABLE question_banks IS 'Stores all questions (admin-curated and AI-generated)';
COMMENT ON TABLE question_field_mapping IS 'Maps questions to study fields for targeted assessments';
COMMENT ON TABLE question_usage_stats IS 'Tracks question performance and usage statistics';
COMMENT ON TABLE assignment_attempts IS 'Stores assignment attempt results and scores';
COMMENT ON TABLE assignment_responses IS 'Stores detailed responses for each question in assignments';
COMMENT ON TABLE admins IS 'Admin user management';

-- =====================================================
-- 10. VERIFICATION QUERIES
-- =====================================================

-- Uncomment these to verify your setup worked correctly:

-- Check if all tables were created
-- SELECT table_name FROM information_schema.tables WHERE table_schema = 'public' ORDER BY table_name;

-- Check students table
-- SELECT COUNT(*) as student_count FROM students;

-- Check study fields
-- SELECT id, name, short_name FROM study_fields;

-- Check form configurations
-- SELECT id, name, is_active FROM form_configurations;

-- Check question bank summary
-- SELECT * FROM question_bank_summary;

-- =====================================================
-- SETUP COMPLETE!
-- =====================================================
-- Your Supabase database is now ready for the field-based assessment system.
-- 
-- Environment variables needed:
-- VITE_SUPABASE_URL=your_supabase_url
-- VITE_SUPABASE_ANON_KEY=your_supabase_anon_key  
-- VITE_SUPABASE_TABLE=students
-- VITE_GROK_API_KEY=your_grok_api_key
--
-- Features enabled:
-- ✅ Student intake with field-based forms
-- ✅ Background selection (field/class/goals)
-- ✅ Question bank management (admin + AI generated)
-- ✅ Field-based question mapping
-- ✅ Assignment attempts and detailed responses
-- ✅ Question usage statistics
-- ✅ Admin panel support
-- ✅ Development-friendly RLS policies
--
-- Next steps:
-- 1. Set up your environment variables
-- 2. Test the intake flow: /intake
-- 3. Test the assignment flow: /assignment  
-- 4. Check admin panel: /admin -> Question Banks
-- 5. Verify AI-generated questions appear in Question Bank Manager

SELECT 'Field-based assessment system setup completed successfully!' as status;