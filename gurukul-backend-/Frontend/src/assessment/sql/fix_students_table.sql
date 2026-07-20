-- =====================================================
-- FIX STUDENTS TABLE - ADD MISSING COLUMNS
-- =====================================================
-- Run this if you already have a students table but missing columns

-- Add user_id column if it doesn't exist
DO $$ 
BEGIN 
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name = 'students' AND column_name = 'user_id') THEN
        ALTER TABLE students ADD COLUMN user_id TEXT;
    END IF;
END $$;

-- Add student_id column if it doesn't exist
DO $$ 
BEGIN 
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name = 'students' AND column_name = 'student_id') THEN
        ALTER TABLE students ADD COLUMN student_id TEXT;
    END IF;
END $$;

-- Add grade column if it doesn't exist
DO $$ 
BEGIN 
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name = 'students' AND column_name = 'grade') THEN
        ALTER TABLE students ADD COLUMN grade TEXT;
    END IF;
END $$;

-- Add tier column if it doesn't exist
DO $$ 
BEGIN 
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name = 'students' AND column_name = 'tier') THEN
        ALTER TABLE students ADD COLUMN tier TEXT CHECK (tier IN ('Seed', 'Tree', 'Sky'));
    END IF;
END $$;

-- Add responses column if it doesn't exist
DO $$ 
BEGIN 
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name = 'students' AND column_name = 'responses') THEN
        ALTER TABLE students ADD COLUMN responses JSONB DEFAULT '{}'::jsonb;
    END IF;
END $$;

-- Add created_at column if it doesn't exist
DO $$ 
BEGIN 
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name = 'students' AND column_name = 'created_at') THEN
        ALTER TABLE students ADD COLUMN created_at TIMESTAMPTZ DEFAULT NOW();
    END IF;
END $$;

-- Add updated_at column if it doesn't exist
DO $$ 
BEGIN 
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name = 'students' AND column_name = 'updated_at') THEN
        ALTER TABLE students ADD COLUMN updated_at TIMESTAMPTZ DEFAULT NOW();
    END IF;
END $$;

-- Create indexes if they don't exist
CREATE INDEX IF NOT EXISTS idx_students_email ON students(email);
CREATE INDEX IF NOT EXISTS idx_students_user_id ON students(user_id);
CREATE INDEX IF NOT EXISTS idx_students_tier ON students(tier);
CREATE INDEX IF NOT EXISTS idx_students_created_at ON students(created_at);
CREATE INDEX IF NOT EXISTS idx_students_updated_at ON students(updated_at);
CREATE INDEX IF NOT EXISTS idx_students_responses ON students USING GIN (responses);

-- Enable RLS if not already enabled
ALTER TABLE students ENABLE ROW LEVEL SECURITY;

-- Drop existing policies if they exist and recreate
DROP POLICY IF EXISTS "Allow all operations for authenticated users on students" ON students;
CREATE POLICY "Allow all operations for authenticated users on students" ON students
  FOR ALL USING (true);

-- Create or replace the update trigger function
CREATE OR REPLACE FUNCTION update_students_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Drop existing trigger if it exists and recreate
DROP TRIGGER IF EXISTS update_students_updated_at ON students;
CREATE TRIGGER update_students_updated_at 
    BEFORE UPDATE ON students 
    FOR EACH ROW 
    EXECUTE FUNCTION update_students_updated_at_column();

-- Verify the table structure
SELECT column_name, data_type, is_nullable 
FROM information_schema.columns 
WHERE table_name = 'students' 
ORDER BY ordinal_position;
