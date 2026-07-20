-- Setup Dynamic Study Fields System
-- Run this in your Supabase SQL Editor

-- First, check if study_fields table exists and what structure it has
DO $$
BEGIN
    -- Check if the table exists
    IF EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'study_fields') THEN
        RAISE NOTICE 'study_fields table exists, checking structure...';
        
        -- Check if it has the old structure (id as TEXT primary key)
        IF EXISTS (SELECT FROM information_schema.columns 
                  WHERE table_name = 'study_fields' 
                  AND column_name = 'id' 
                  AND data_type = 'text') THEN
            RAISE NOTICE 'Found old structure with TEXT id, updating...';
            
            -- Add new columns if they don't exist
            IF NOT EXISTS (SELECT FROM information_schema.columns 
                          WHERE table_name = 'study_fields' AND column_name = 'field_id') THEN
                ALTER TABLE study_fields ADD COLUMN field_id TEXT;
                UPDATE study_fields SET field_id = id WHERE field_id IS NULL;
                ALTER TABLE study_fields ALTER COLUMN field_id SET NOT NULL;
                CREATE UNIQUE INDEX IF NOT EXISTS idx_study_fields_field_id_unique ON study_fields(field_id);
            END IF;
            
            IF NOT EXISTS (SELECT FROM information_schema.columns 
                          WHERE table_name = 'study_fields' AND column_name = 'icon') THEN
                ALTER TABLE study_fields ADD COLUMN icon TEXT NOT NULL DEFAULT '📚';
            END IF;
            
            IF NOT EXISTS (SELECT FROM information_schema.columns 
                          WHERE table_name = 'study_fields' AND column_name = 'color') THEN
                ALTER TABLE study_fields ADD COLUMN color TEXT NOT NULL DEFAULT 'text-gray-400 bg-gray-400/10 border-gray-400/20';
            END IF;
            
            IF NOT EXISTS (SELECT FROM information_schema.columns 
                          WHERE table_name = 'study_fields' AND column_name = 'is_active') THEN
                ALTER TABLE study_fields ADD COLUMN is_active BOOLEAN DEFAULT TRUE;
            END IF;
            
        ELSE
            RAISE NOTICE 'Table has different structure, will create new columns as needed';
        END IF;
    ELSE
        RAISE NOTICE 'study_fields table does not exist, creating new table...';
    END IF;
END $$;

-- Create or update study_fields table for dynamic field management
CREATE TABLE IF NOT EXISTS study_fields (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  field_id TEXT UNIQUE NOT NULL,
  name TEXT NOT NULL,
  icon TEXT NOT NULL DEFAULT '📚',
  description TEXT,
  color TEXT NOT NULL DEFAULT 'text-gray-400 bg-gray-400/10 border-gray-400/20',
  is_active BOOLEAN DEFAULT TRUE,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_study_fields_field_id ON study_fields(field_id);
CREATE INDEX IF NOT EXISTS idx_study_fields_active ON study_fields(is_active);

-- Enable RLS
ALTER TABLE study_fields ENABLE ROW LEVEL SECURITY;

-- Drop existing policies if they exist
DROP POLICY IF EXISTS "Allow all operations on study_fields for development" ON study_fields;
DROP POLICY IF EXISTS "Anyone can view study fields" ON study_fields;
DROP POLICY IF EXISTS "Allow all operations for development" ON study_fields;

-- Create RLS policies for development (allow all operations)
CREATE POLICY "Allow all operations on study_fields for development" ON study_fields
    FOR ALL TO PUBLIC USING (true);

-- Create trigger for updated_at
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

DROP TRIGGER IF EXISTS update_study_fields_updated_at ON study_fields;
CREATE TRIGGER update_study_fields_updated_at 
    BEFORE UPDATE ON study_fields 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Insert/Update default study fields with proper icons and colors
INSERT INTO study_fields (field_id, name, icon, description, color, is_active, created_at, updated_at)
VALUES 
  ('stem', 'STEM', '🔬', 'Science, Technology, Engineering, and Mathematics', 'text-blue-400 bg-blue-400/10 border-blue-400/20', true, NOW(), NOW()),
  ('business', 'Business', '💼', 'Business and Economics', 'text-green-400 bg-green-400/10 border-green-400/20', true, NOW(), NOW()),
  ('social_sciences', 'Social Sciences', '🏛️', 'Social Sciences and Humanities', 'text-purple-400 bg-purple-400/10 border-purple-400/20', true, NOW(), NOW()),
  ('health_medicine', 'Health & Medicine', '⚕️', 'Healthcare and Medical Sciences', 'text-red-400 bg-red-400/10 border-red-400/20', true, NOW(), NOW()),
  ('creative_arts', 'Creative Arts', '🎨', 'Arts, Design, and Creative Fields', 'text-pink-400 bg-pink-400/10 border-pink-400/20', true, NOW(), NOW())
ON CONFLICT (field_id) DO UPDATE SET
  name = EXCLUDED.name,
  icon = EXCLUDED.icon,
  description = EXCLUDED.description,
  color = EXCLUDED.color,
  is_active = EXCLUDED.is_active,
  updated_at = NOW();

-- If there are existing records without field_id, update them
UPDATE study_fields 
SET field_id = id 
WHERE field_id IS NULL AND id IS NOT NULL;

-- Update existing records to have proper icons and colors if they're missing
UPDATE study_fields SET 
  icon = CASE 
    WHEN field_id = 'stem' OR id = 'stem' THEN '🔬'
    WHEN field_id = 'business' OR id = 'business' THEN '💼'
    WHEN field_id = 'social_sciences' OR id = 'social_sciences' THEN '🏛️'
    WHEN field_id = 'health_medicine' OR id = 'health_medicine' THEN '⚕️'
    WHEN field_id = 'creative_arts' OR id = 'creative_arts' THEN '🎨'
    WHEN field_id = 'other' OR id = 'other' THEN '📚'
    ELSE '📚'
  END,
  color = CASE 
    WHEN field_id = 'stem' OR id = 'stem' THEN 'text-blue-400 bg-blue-400/10 border-blue-400/20'
    WHEN field_id = 'business' OR id = 'business' THEN 'text-green-400 bg-green-400/10 border-green-400/20'
    WHEN field_id = 'social_sciences' OR id = 'social_sciences' THEN 'text-purple-400 bg-purple-400/10 border-purple-400/20'
    WHEN field_id = 'health_medicine' OR id = 'health_medicine' THEN 'text-red-400 bg-red-400/10 border-red-400/20'
    WHEN field_id = 'creative_arts' OR id = 'creative_arts' THEN 'text-pink-400 bg-pink-400/10 border-pink-400/20'
    WHEN field_id = 'other' OR id = 'other' THEN 'text-gray-400 bg-gray-400/10 border-gray-400/20'
    ELSE 'text-gray-400 bg-gray-400/10 border-gray-400/20'
  END,
  is_active = COALESCE(is_active, true),
  updated_at = NOW()
WHERE icon IS NULL OR icon = '' OR color IS NULL OR color = '';

-- Verify the setup
SELECT 
  field_id,
  name,
  icon,
  description,
  color,
  is_active,
  created_at
FROM study_fields 
ORDER BY created_at;

-- Success message
SELECT 'Dynamic Study Fields system setup complete! Admins can now add custom fields.' as status;