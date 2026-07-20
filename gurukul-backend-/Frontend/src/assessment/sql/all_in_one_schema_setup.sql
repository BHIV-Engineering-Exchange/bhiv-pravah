-- All-in-one Supabase schema setup for Gurukul intake + admin form builder
-- Safe to run multiple times (uses IF NOT EXISTS and CREATE OR REPLACE)

-- 0) Extensions required
CREATE EXTENSION IF NOT EXISTS pgcrypto; -- for gen_random_uuid()

-- 1) Shared trigger function for updated_at management
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = NOW();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- 2) form_configurations: stores admin-saved form configs rendered by /intake
CREATE TABLE IF NOT EXISTS form_configurations (
  id TEXT PRIMARY KEY,
  name TEXT NOT NULL,
  description TEXT,
  fields JSONB NOT NULL DEFAULT '[]'::jsonb,
  is_active BOOLEAN DEFAULT false,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_form_configurations_active ON form_configurations(is_active);
CREATE INDEX IF NOT EXISTS idx_form_configurations_updated_at ON form_configurations(updated_at);

-- RLS
ALTER TABLE form_configurations ENABLE ROW LEVEL SECURITY;
DO $$ BEGIN
  BEGIN
    CREATE POLICY "Allow all operations for authenticated users on form_configurations"
    ON form_configurations FOR ALL USING (true);
  EXCEPTION WHEN duplicate_object THEN NULL; END;
END $$;

-- Triggers
DROP TRIGGER IF EXISTS update_form_configurations_updated_at ON form_configurations;
CREATE TRIGGER update_form_configurations_updated_at
  BEFORE UPDATE ON form_configurations
  FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- 3) students: stores student submissions; form values go into responses JSONB
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

-- Indexes
CREATE INDEX IF NOT EXISTS idx_students_email ON students(email);
CREATE INDEX IF NOT EXISTS idx_students_user_id ON students(user_id);
CREATE INDEX IF NOT EXISTS idx_students_tier ON students(tier);
CREATE INDEX IF NOT EXISTS idx_students_created_at ON students(created_at);
CREATE INDEX IF NOT EXISTS idx_students_updated_at ON students(updated_at);
CREATE INDEX IF NOT EXISTS idx_students_responses ON students USING GIN (responses);

-- RLS
ALTER TABLE students ENABLE ROW LEVEL SECURITY;
DO $$ BEGIN
  BEGIN
    CREATE POLICY "Allow all operations for authenticated users on students"
    ON students FOR ALL USING (true);
  EXCEPTION WHEN duplicate_object THEN NULL; END;
END $$;

-- Triggers
DROP TRIGGER IF EXISTS update_students_updated_at ON students;
CREATE TRIGGER update_students_updated_at
  BEFORE UPDATE ON students
  FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- 4) study_fields: dynamic options for Field of Study (used by DynamicFieldService)
CREATE TABLE IF NOT EXISTS study_fields (
  field_id TEXT PRIMARY KEY,
  name TEXT NOT NULL,
  icon TEXT,
  description TEXT,
  color TEXT,
  is_active BOOLEAN DEFAULT TRUE,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_study_fields_active ON study_fields(is_active);

-- RLS
ALTER TABLE study_fields ENABLE ROW LEVEL SECURITY;
DO $$ BEGIN
  BEGIN
    CREATE POLICY "Allow all operations for authenticated users on study_fields"
    ON study_fields FOR ALL USING (true);
  EXCEPTION WHEN duplicate_object THEN NULL; END;
END $$;

-- Triggers
DROP TRIGGER IF EXISTS update_study_fields_updated_at ON study_fields;
CREATE TRIGGER update_study_fields_updated_at
  BEFORE UPDATE ON study_fields
  FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- 5) dynamic_question_categories: dynamic categories for classification metadata in builder
CREATE TABLE IF NOT EXISTS dynamic_question_categories (
  category_id TEXT PRIMARY KEY,
  name TEXT NOT NULL,
  icon TEXT,
  color TEXT,
  display_order INT DEFAULT 0,
  is_system BOOLEAN DEFAULT FALSE,
  is_active BOOLEAN DEFAULT TRUE,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_dynamic_categories_order ON dynamic_question_categories(display_order);
CREATE INDEX IF NOT EXISTS idx_dynamic_categories_active ON dynamic_question_categories(is_active);

-- RLS
ALTER TABLE dynamic_question_categories ENABLE ROW LEVEL SECURITY;
DO $$ BEGIN
  BEGIN
    CREATE POLICY "Allow all operations for authenticated users on dynamic_question_categories"
    ON dynamic_question_categories FOR ALL USING (true);
  EXCEPTION WHEN duplicate_object THEN NULL; END;
END $$;

-- Triggers
DROP TRIGGER IF EXISTS update_dynamic_categories_updated_at ON dynamic_question_categories;
CREATE TRIGGER update_dynamic_categories_updated_at
  BEFORE UPDATE ON dynamic_question_categories
  FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- 6) question_field_mapping: optional mapping table for stats (used by DynamicFieldService)
CREATE TABLE IF NOT EXISTS question_field_mapping (
  id BIGSERIAL PRIMARY KEY,
  question_id TEXT NOT NULL,
  field_id TEXT NOT NULL REFERENCES study_fields(field_id) ON UPDATE CASCADE ON DELETE RESTRICT,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_qfm_field_id ON question_field_mapping(field_id);

-- RLS
ALTER TABLE question_field_mapping ENABLE ROW LEVEL SECURITY;
DO $$ BEGIN
  BEGIN
    CREATE POLICY "Allow all operations for authenticated users on question_field_mapping"
    ON question_field_mapping FOR ALL USING (true);
  EXCEPTION WHEN duplicate_object THEN NULL; END;
END $$;

-- 7) background_selections: optional separate store for background; assignment reads it if present
CREATE TABLE IF NOT EXISTS background_selections (
  id BIGSERIAL PRIMARY KEY,
  user_id TEXT UNIQUE NOT NULL,
  field_of_study VARCHAR(255) NOT NULL,
  class_level VARCHAR(255) NOT NULL,
  learning_goals VARCHAR(255) NOT NULL,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_background_selections_user_id ON background_selections(user_id);

-- RLS
ALTER TABLE background_selections ENABLE ROW LEVEL SECURITY;
DO $$ BEGIN
  BEGIN
    CREATE POLICY "Allow all operations for authenticated users on background_selections"
    ON background_selections FOR ALL USING (true);
  EXCEPTION WHEN duplicate_object THEN NULL; END;
END $$;

-- Triggers
DROP TRIGGER IF EXISTS update_background_selections_updated_at ON background_selections;
CREATE TRIGGER update_background_selections_updated_at
  BEFORE UPDATE ON background_selections
  FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- 8) Verification helpers (optional selects) - safe to run when testing
-- Uncomment in Supabase SQL editor to verify
-- SELECT id, name, is_active, jsonb_array_length(fields) AS field_count FROM form_configurations ORDER BY updated_at DESC LIMIT 3;
-- SELECT id, email, responses ? 'field_of_study' AS has_field_of_study, responses ? 'class_level' AS has_class_level, responses ? 'learning_goals' AS has_learning_goals FROM students LIMIT 5;
-- SELECT field_id, name, is_active FROM study_fields ORDER BY created_at ASC LIMIT 10;
-- SELECT category_id, name, is_active FROM dynamic_question_categories ORDER BY display_order ASC LIMIT 10;
-- SELECT to_regclass('public.background_selections');
